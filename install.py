#!/usr/bin/env python3
"""install.py - install (or remove) the usage-tracker skill in Claude Code. Python 3 standard library only.

  python3 install.py               install: copy the scripts to <config>/usage-tracker/bin/, merge statusLine + hook into settings.json
  python3 install.py --dry-run     only print what would be done, write nothing
  python3 install.py --uninstall   remove: delete only the entries it added and the bin files the skill created; keep the data and the config directory
  python3 install.py --config-dir <dir>   (default: CLAUDE_CONFIG_DIR or ~/.claude)

Safety:
- Backs up settings.json before editing (settings.json.usage-tracker.<time>.bak).
- settings.json unreadable (broken JSON) -> stop, write nothing.
- You already have another statusLine -> NOT overwritten; prints how to chain it (statusline_usage.py --quiet).
- UserPromptSubmit hook: adds one new group and keeps your existing hooks.
- Keeps every other key of settings.json.
"""
import json
import os
import shutil
import sys
import time

GOC = os.path.dirname(os.path.abspath(__file__))
TEP_SCRIPT = ("usage_chung.py", "statusline_usage.py", "nhip_tuan.py", "hook_usage.py")
DAU = "usage-tracker"  # marker used to recognise the entries this skill added


def tham_so(ten):
    a = sys.argv[1:]
    if ten in a:
        i = a.index(ten)
        return a[i + 1] if i + 1 < len(a) else None
    return None


def thu_muc_cau_hinh():
    v = tham_so("--config-dir") or os.environ.get("CLAUDE_CONFIG_DIR", "").strip().strip('"')
    return os.path.abspath(os.path.expanduser(v)) if v else os.path.join(os.path.expanduser("~"), ".claude")


def lenh(py, tep):
    return '"%s" "%s"' % (py, tep)


def la_cua_ta(c):
    return isinstance(c, str) and DAU in c.replace("\\", "/") and "/bin/" in c.replace("\\", "/")


def doc_settings(duong_dan):
    if not os.path.exists(duong_dan):
        return {}
    with open(duong_dan, encoding="utf-8") as f:
        d = json.load(f)  # broken JSON -> exception -> stop
    if not isinstance(d, dict):
        raise ValueError("settings.json is not a JSON object")
    return d


def ghi_settings(duong_dan, d):
    tam = duong_dan + ".tmp"
    with open(tam, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tam, duong_dan)


def cai(cfg, dry):
    sp = os.path.join(cfg, "settings.json")
    bin_dir = os.path.join(cfg, DAU, "bin")
    py = sys.executable
    lenh_sl = lenh(py, os.path.join(bin_dir, "statusline_usage.py"))
    lenh_hk = lenh(py, os.path.join(bin_dir, "hook_usage.py"))
    try:
        st = doc_settings(sp)
    except Exception as e:
        print("STOP: cannot read %s (%s). Nothing written." % (sp, type(e).__name__))
        return 2
    kq = []
    # 1) statusLine
    cu = st.get("statusLine")
    if cu is None:
        st["statusLine"] = {"type": "command", "command": lenh_sl}
        kq.append("statusLine: set (new)")
    elif isinstance(cu, dict) and la_cua_ta(cu.get("command")):
        cu["command"] = lenh_sl
        kq.append("statusLine: updated the skill's own entry")
    else:
        kq.append("statusLine: you ALREADY HAVE one, not overwritten.")
        kq.append("  To chain: in your status-line script, forward the stdin JSON to this command (it prints nothing):")
        kq.append("    " + lenh_sl + " --quiet")
        kq.append("  or run that command and print its line: drop --quiet. To replace yours entirely: edit the statusLine key in settings.json by hand.")
    # 2) hook UserPromptSubmit
    hooks = st.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        print("STOP: the hooks key in settings.json is not an object. Nothing written.")
        return 2
    ds = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(ds, list):
        print("STOP: hooks.UserPromptSubmit is not a list. Nothing written.")
        return 2
    da = False
    for nhom in ds:
        for h in (nhom.get("hooks") if isinstance(nhom, dict) else None) or []:
            if isinstance(h, dict) and la_cua_ta(h.get("command")):
                h["command"] = lenh_hk
                da = True
    if not da:
        ds.append({"hooks": [{"type": "command", "command": lenh_hk}]})
        kq.append("hook UserPromptSubmit: added a new group (kept %d existing groups)" % (len(ds) - 1))
    else:
        kq.append("hook UserPromptSubmit: updated the skill's own entry")
    kq.append("copy %d files to %s" % (len(TEP_SCRIPT), bin_dir))
    if dry:
        print("[dry-run] nothing written. Would do:")
        for d in kq:
            print(" -", d)
        return 0
    os.makedirs(bin_dir, exist_ok=True)
    for t in TEP_SCRIPT:
        shutil.copyfile(os.path.join(GOC, "scripts", t), os.path.join(bin_dir, t))
    if os.path.exists(sp):
        bak = "%s.usage-tracker.%s.bak" % (sp, time.strftime("%Y%m%d-%H%M%S"))
        shutil.copyfile(sp, bak)
        kq.append("backup: " + bak)
    os.makedirs(cfg, exist_ok=True)
    ghi_settings(sp, st)
    for d in kq:
        print(" -", d)
    print("Done. Restart Claude Code; the status line shows numbers after the first message.")
    return 0


def go(cfg, dry):
    sp = os.path.join(cfg, "settings.json")
    bin_dir = os.path.join(cfg, DAU, "bin")
    try:
        st = doc_settings(sp)
    except Exception as e:
        print("STOP: cannot read %s (%s). Nothing written." % (sp, type(e).__name__))
        return 2
    kq = []
    cu = st.get("statusLine")
    if isinstance(cu, dict) and la_cua_ta(cu.get("command")):
        del st["statusLine"]
        kq.append("removed the skill's statusLine")
    hooks = st.get("hooks")
    ds = hooks.get("UserPromptSubmit") if isinstance(hooks, dict) else None
    if isinstance(ds, list):
        moi = []
        for nhom in ds:
            hs = nhom.get("hooks") if isinstance(nhom, dict) else None
            if isinstance(hs, list):
                con = [h for h in hs if not (isinstance(h, dict) and la_cua_ta(h.get("command")))]
                if len(con) != len(hs):
                    kq.append("removed the skill's hook")
                    if not con and set(nhom.keys()) <= {"hooks", "matcher"}:
                        continue
                    nhom["hooks"] = con
            moi.append(nhom)
        if moi:
            hooks["UserPromptSubmit"] = moi
        elif ds:
            del hooks["UserPromptSubmit"]
            if not hooks:
                del st["hooks"]
    tep_xoa = [os.path.join(bin_dir, t) for t in TEP_SCRIPT + ("lang_vi.py",) if os.path.exists(os.path.join(bin_dir, t))]
    kq.append("delete %d bin files created by the skill (keeping the data rate.json, moc.jsonl and the config directory)" % len(tep_xoa))
    if dry:
        print("[dry-run] nothing written. Would do:")
        for d in kq:
            print(" -", d)
        return 0
    if os.path.exists(sp):
        bak = "%s.usage-tracker.%s.bak" % (sp, time.strftime("%Y%m%d-%H%M%S"))
        shutil.copyfile(sp, bak)
        kq.append("backup: " + bak)
        ghi_settings(sp, st)
    for t in tep_xoa:
        os.remove(t)
    pc = os.path.join(bin_dir, "__pycache__")
    try:
        if os.path.isdir(pc):
            shutil.rmtree(pc)  # generated by Python when the scripts in bin run
        os.rmdir(bin_dir)  # only removed if empty
    except OSError:
        pass
    for d in kq:
        print(" -", d)
    return 0


if __name__ == "__main__":
    cfg = thu_muc_cau_hinh()
    dry = "--dry-run" in sys.argv[1:]
    sys.exit(go(cfg, dry) if "--uninstall" in sys.argv[1:] else cai(cfg, dry))
