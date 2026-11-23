#!/usr/bin/env python3
"""install.py - install (or remove) the usage-tracker skill in Claude Code. Python 3 standard library only.

  python3 install.py               install: copy the scripts to <config>/usage-tracker/bin/, merge statusLine + hook into settings.json
  python3 install.py --dry-run     only print what would be done, write nothing
  python3 install.py --uninstall   remove: delete only the entries it added and the bin files the skill created; keep the data and the config directory
  python3 install.py --config-dir <dir>   (default: CLAUDE_CONFIG_DIR or ~/.claude)
  python3 install.py --codex       Codex CLI instead: set [tui] status_line in <codex home>/config.toml
                                   (codex home = CODEX_HOME or ~/.codex); works with --dry-run and --uninstall

Safety:
- Backs up settings.json before editing (settings.json.usage-tracker.<time>.bak).
- settings.json unreadable (broken JSON) -> stop, write nothing.
- You already have another statusLine -> NOT overwritten; prints how to chain it (statusline_usage.py --quiet).
- UserPromptSubmit hook: adds one new group and keeps your existing hooks.
- Keeps every other key of settings.json.
- Codex: backs up config.toml (config.toml.usage-tracker.<time>.bak), edits only the status_line key of [tui],
  never overwrites a status_line you set yourself, and --uninstall removes it only if it is still this one.
"""
import json
import os
import re
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


# ---------------- Codex CLI ----------------
CODEX_ITEMS = ["project-name", "model-with-reasoning", "context-used", "weekly-limit", "five-hour-limit"]
RE_TUI = re.compile(r"^\s*\[\s*tui\s*\]\s*(#.*)?$")
RE_BANG = re.compile(r"^\s*\[")
RE_KHOA = re.compile(r"^\s*status_line\s*=")


def dong_codex(items):
    return "status_line = [%s]" % ", ".join('"%s"' % i for i in items)


def tim_status_line(dong):
    """(start_tui, end_tui, i, j) of the status_line key inside [tui]; None parts when absent."""
    s = next((k for k, l in enumerate(dong) if RE_TUI.match(l)), None)
    if s is None:
        return None, None, None, None
    e = next((k for k in range(s + 1, len(dong)) if RE_BANG.match(dong[k])), len(dong))
    for i in range(s + 1, e):
        if RE_KHOA.match(dong[i]):
            j, sau = i, dong[i].count("[") - dong[i].count("]")
            while sau > 0 and j + 1 < e:  # multi-line array
                j += 1
                sau += dong[j].count("[") - dong[j].count("]")
            return s, e, i, j
    return s, e, None, None


def codex_sua(text, go_bo=False):
    """Return (new_text or None if refused, message). Pure function, tested in tests/kiem_thu.py."""
    dong = text.splitlines()
    ours = dong_codex(CODEX_ITEMS)
    s, e, i, j = tim_status_line(dong)
    hien = " ".join(x.strip() for x in dong[i:j + 1]) if i is not None else None
    la_ta = hien is not None and hien.replace(" ", "") == ours.replace(" ", "")
    if go_bo:
        if not la_ta:
            return text, "status_line: not set by usage-tracker, left alone"
        return "\n".join(dong[:i] + dong[j + 1:]) + "\n", "status_line: removed"
    if la_ta:
        return text, "status_line: already set"
    if hien is not None:
        return None, "status_line: you ALREADY HAVE one, not overwritten: " + hien
    if s is None:
        sep = "" if not text or text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        return text + sep + "[tui]\n" + ours + "\n", "status_line: added a [tui] table"
    return "\n".join(dong[:s + 1] + [ours] + dong[s + 1:]) + "\n", "status_line: added to [tui]"


def codex(dry, go_bo):
    home = os.environ.get("CODEX_HOME", "").strip().strip('"') or os.path.join(os.path.expanduser("~"), ".codex")
    tep = os.path.join(os.path.abspath(os.path.expanduser(home)), "config.toml")
    text = ""
    if os.path.exists(tep):
        with open(tep, encoding="utf-8") as f:
            text = f.read()
    moi, msg = codex_sua(text, go_bo)
    print(" - Codex %s: %s" % (tep, msg))
    if moi is None:
        print("   To use this one instead, replace that line by hand with:  " + dong_codex(CODEX_ITEMS))
        return 0
    if moi == text or dry:
        if dry:
            print("[dry-run] nothing written.")
        return 0
    if os.path.exists(tep):
        bak = "%s.usage-tracker.%s.bak" % (tep, time.strftime("%Y%m%d-%H%M%S"))
        shutil.copyfile(tep, bak)
        print(" - backup: " + bak)
    os.makedirs(os.path.dirname(tep), exist_ok=True)
    tam = tep + ".tmp"
    with open(tam, "w", encoding="utf-8", newline="\n") as f:
        f.write(moi)
    os.replace(tam, tep)
    print("Done. Restart Codex to see the status line.")
    return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv[1:]
    if "--codex" in sys.argv[1:]:
        sys.exit(codex(dry, "--uninstall" in sys.argv[1:]))
    cfg = thu_muc_cau_hinh()
    sys.exit(go(cfg, dry) if "--uninstall" in sys.argv[1:] else cai(cfg, dry))
