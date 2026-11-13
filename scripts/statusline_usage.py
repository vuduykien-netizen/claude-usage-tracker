#!/usr/bin/env python3
"""statusline_usage.py - Claude Code status line: 7-day limit, Fable, weekly pace.

Reads the statusLine JSON from stdin (only the rate_limits field), writes <config>/usage-tracker/rate.json,
and prints ONE ASCII line:  7d Fable usage 17% | 7d usage 56% | 7d time 48% | YELLOW
(the light is GREEN / YELLOW / RED / SPARE; the Fable part appears only when it is known)
  --quiet : only write the data, print nothing (to chain into your existing status line)
Never reads conversation content, never uses the network, never overwrites old data when a key is missing or the JSON is broken.
Never raises (a status line must not break).
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
    d7 = uc.cua_so(rl, "seven_day")
    khac = {}
    if isinstance(rl, dict):
        for k in rl:
            if k not in uc.CUA_SO_CHINH and k not in uc.BO_QUA:
                w = uc.cua_so(rl, k)
                if w:
                    khac[TEN_AN_TOAN.sub("_", str(k))[:40]] = w
    if d7 is None and not khac:
        if not quiet:
            print("Usage -")
        return
    cu = uc.doc_rate() or {}
    # a window missing this time: keep the old value if that window has not expired

    def giu(moi, khoa):
        if moi is not None:
            return moi
        w = cu.get(khoa)
        if isinstance(w, dict) and uc.la_so(w.get("resets")) and w["resets"] > now:
            return w
        return None

    rate = {"t": int(now), "seven_day": giu(d7, "seven_day"), "khac": khac}
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
