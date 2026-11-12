#!/usr/bin/env python3
"""install.py - cai (hoac go) skill theo-doi-usage vao Claude Code. Chi thu vien chuan Python 3.

  python3 install.py               cai: chep scripts vao <cau hinh>/usage-tracker/bin/, gop statusLine + hook vao settings.json
  python3 install.py --dry-run     chi in dieu se lam, khong ghi gi
  python3 install.py --uninstall   go: chi xoa dung muc da them va dung cac tep bin do skill tao; giu du lieu va thu muc cau hinh
  python3 install.py --config-dir <thu muc>   (mac dinh: CLAUDE_CONFIG_DIR hoac ~/.claude)

An toan:
- Sao luu settings.json truoc khi sua (settings.json.usage-tracker.<thoi gian>.bak).
- settings.json khong doc duoc (JSON hong) -> dung, khong ghi gi.
- Da co statusLine khac cua ban -> KHONG ghi de, in huong dan noi (statusline_usage.py --quiet).
- Hook UserPromptSubmit: them mot nhom moi, giu nguyen cac hook san co.
- Giu nguyen moi khoa khac cua settings.json.
"""
import json
import os
import shutil
import sys
import time

GOC = os.path.dirname(os.path.abspath(__file__))
TEP_SCRIPT = ("usage_chung.py", "statusline_usage.py", "nhip_tuan.py", "hook_usage.py")
DAU = "usage-tracker"  # dau hieu nhan ra muc do skill them


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
        d = json.load(f)  # JSON hong -> ngoai le -> dung
    if not isinstance(d, dict):
        raise ValueError("settings.json khong phai doi tuong JSON")
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
        print("DUNG: khong doc duoc %s (%s). Khong ghi gi." % (sp, type(e).__name__))
        return 2
    kq = []
    # 1) statusLine
    cu = st.get("statusLine")
    if cu is None:
        st["statusLine"] = {"type": "command", "command": lenh_sl}
        kq.append("statusLine: dat moi")
    elif isinstance(cu, dict) and la_cua_ta(cu.get("command")):
        cu["command"] = lenh_sl
        kq.append("statusLine: cap nhat ban cua skill")
    else:
        kq.append("statusLine: DA CO cua ban, khong ghi de.")
        kq.append("  De noi: trong script thanh trang thai cua ban, chuyen tiep JSON stdin sang lenh nay (khong in gi):")
        kq.append("    " + lenh_sl + " --quiet")
        kq.append("  hoac chay lenh do va in dong: bo --quiet. Muon thay han: sua tay khoa statusLine trong settings.json.")
    # 2) hook UserPromptSubmit
    hooks = st.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        print("DUNG: khoa hooks trong settings.json khong phai doi tuong. Khong ghi gi.")
        return 2
    ds = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(ds, list):
        print("DUNG: hooks.UserPromptSubmit khong phai danh sach. Khong ghi gi.")
        return 2
    da = False
    for nhom in ds:
        for h in (nhom.get("hooks") if isinstance(nhom, dict) else None) or []:
            if isinstance(h, dict) and la_cua_ta(h.get("command")):
                h["command"] = lenh_hk
                da = True
    if not da:
        ds.append({"hooks": [{"type": "command", "command": lenh_hk}]})
        kq.append("hook UserPromptSubmit: them nhom moi (giu %d nhom san co)" % (len(ds) - 1))
    else:
        kq.append("hook UserPromptSubmit: cap nhat ban cua skill")
    kq.append("chep %d tep vao %s" % (len(TEP_SCRIPT), bin_dir))
    if dry:
        print("[dry-run] khong ghi gi. Se lam:")
        for d in kq:
            print(" -", d)
        return 0
    os.makedirs(bin_dir, exist_ok=True)
    for t in TEP_SCRIPT:
        shutil.copyfile(os.path.join(GOC, "scripts", t), os.path.join(bin_dir, t))
    if os.path.exists(sp):
        bak = "%s.usage-tracker.%s.bak" % (sp, time.strftime("%Y%m%d-%H%M%S"))
        shutil.copyfile(sp, bak)
        kq.append("sao luu: " + bak)
    os.makedirs(cfg, exist_ok=True)
    ghi_settings(sp, st)
    for d in kq:
        print(" -", d)
    print("Xong. Mo lai Claude Code; thanh trang thai co so sau tin nhan dau tien.")
    return 0


def go(cfg, dry):
    sp = os.path.join(cfg, "settings.json")
    bin_dir = os.path.join(cfg, DAU, "bin")
    try:
        st = doc_settings(sp)
    except Exception as e:
        print("DUNG: khong doc duoc %s (%s). Khong ghi gi." % (sp, type(e).__name__))
        return 2
    kq = []
    cu = st.get("statusLine")
    if isinstance(cu, dict) and la_cua_ta(cu.get("command")):
        del st["statusLine"]
        kq.append("xoa statusLine cua skill")
    hooks = st.get("hooks")
    ds = hooks.get("UserPromptSubmit") if isinstance(hooks, dict) else None
    if isinstance(ds, list):
        moi = []
        for nhom in ds:
            hs = nhom.get("hooks") if isinstance(nhom, dict) else None
            if isinstance(hs, list):
                con = [h for h in hs if not (isinstance(h, dict) and la_cua_ta(h.get("command")))]
                if len(con) != len(hs):
                    kq.append("go hook cua skill")
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
    tep_xoa = [os.path.join(bin_dir, t) for t in TEP_SCRIPT if os.path.exists(os.path.join(bin_dir, t))]
    kq.append("xoa %d tep bin do skill tao (giu du lieu rate.json, moc.jsonl va thu muc cau hinh)" % len(tep_xoa))
    if dry:
        print("[dry-run] khong ghi gi. Se lam:")
        for d in kq:
            print(" -", d)
        return 0
    if os.path.exists(sp):
        bak = "%s.usage-tracker.%s.bak" % (sp, time.strftime("%Y%m%d-%H%M%S"))
        shutil.copyfile(sp, bak)
        kq.append("sao luu: " + bak)
        ghi_settings(sp, st)
    for t in tep_xoa:
        os.remove(t)
    pc = os.path.join(bin_dir, "__pycache__")
    try:
        if os.path.isdir(pc):
            shutil.rmtree(pc)  # do Python tu sinh khi chay script trong bin
        os.rmdir(bin_dir)  # chi xoa neu rong
    except OSError:
        pass
    for d in kq:
        print(" -", d)
    return 0


if __name__ == "__main__":
    cfg = thu_muc_cau_hinh()
    dry = "--dry-run" in sys.argv[1:]
    sys.exit(go(cfg, dry) if "--uninstall" in sys.argv[1:] else cai(cfg, dry))
