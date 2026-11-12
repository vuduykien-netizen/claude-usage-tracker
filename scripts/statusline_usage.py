#!/usr/bin/env python3
"""statusline_usage.py - thanh trang thai Claude Code: han muc 5 gio, 7 ngay, Fable, nhip tuan.

Doc JSON statusLine tu stdin (chi truong rate_limits), ghi <cau hinh>/usage-tracker/rate.json,
in MOT dong ASCII:  Usage 5h 23% | 7d 56% | Fable 17% | 7d time 48% | VANG
  --quiet : chi ghi du lieu, khong in gi (de noi vao thanh trang thai co san cua ban)
Khong doc noi dung hoi thoai, khong goi mang, khong ghi de du lieu cu khi thieu khoa / JSON hong.
Khong bao gio nem loi ra ngoai (thanh trang thai khong duoc vo).
"""
import json
import os
import re
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usage_chung as uc  # noqa: E402

TEN_AN_TOAN = re.compile(r"[^A-Za-z0-9._-]")


def doc_stdin():
    try:
        return json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def chay(quiet):
    now = time.time()
    data = doc_stdin()
    rl = data.get("rate_limits") if isinstance(data, dict) else None
    h5 = uc.cua_so(rl, "five_hour")
    d7 = uc.cua_so(rl, "seven_day")
    khac = {}
    if isinstance(rl, dict):
        for k in rl:
            if k not in uc.CUA_SO_CHINH:
                w = uc.cua_so(rl, k)
                if w:
                    khac[TEN_AN_TOAN.sub("_", str(k))[:40]] = w
    if h5 is None and d7 is None and not khac:
        if not quiet:
            print("Usage -")
        return
    cu = uc.doc_rate() or {}
    # cua so thieu lan nay (vd chi co 7d vi cua so 5h chua mo): giu so cu neu cua so do chua het han

    def giu(moi, khoa):
        if moi is not None:
            return moi
        w = cu.get(khoa)
        if isinstance(w, dict) and uc.la_so(w.get("resets")) and w["resets"] > now:
            return w
        return None

    rate = {"t": int(now), "five_hour": giu(h5, "five_hour"), "seven_day": giu(d7, "seven_day"), "khac": khac}
    uc.ghi_tep(os.path.join(uc.thu_muc_du_lieu(), "rate.json"), json.dumps(rate, ensure_ascii=True))
    uc.lam_moi_nen(now)
    if not quiet:
        print(uc.dong_ngan(rate, uc.doc_cache(now), now))


if __name__ == "__main__":
    q = "--quiet" in sys.argv[1:]
    try:
        chay(q)
    except Exception:
        try:
            if not q:
                print("Usage -")
        except Exception:
            pass
    sys.exit(0)
