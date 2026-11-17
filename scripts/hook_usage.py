#!/usr/bin/env python3
"""hook_usage.py - Claude Code UserPromptSubmit hook: prints ONE usage reminder line per prompt.

Reads <config>/usage-tracker/rate.json (written by statusline_usage.py) and nhip-cache.json (written by nhip_tuan.py).
Claude Code adds this hook's stdout to the context of that turn. It never reads the content of your prompt.
If the pace cache is older than 60 minutes, nhip_tuan.py is started in the background (no waiting). Always exits 0, never raises.
"""
import json
import os
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usage_chung as uc  # noqa: E402

S = {
    "none": "usage: no number yet (status line has not written any)",
    "ago": "{m} min old", "old": " (STALE)", "time": "week {t}% elapsed", "reset": "reset {g}",
    "r7": "7d >=95%: urgent work only",
    "Y": "7d is ahead of schedule: fewer parallel tasks, lighter models",
    "R": "7d is far ahead of schedule: deadline work only",
    "S": "7d has headroom: good time for queued work",
    "light": "light", "fable": "7d Fable usage",
}


def gio(ts):
    return time.strftime("%H:%M %d/%m", time.localtime(ts))


def dong(now, dau=""):
    s = S
    rate = uc.doc_rate()
    if not rate:
        return s["none"]
    cache = uc.doc_cache(now)
    phan, canh = [], []
    w7 = rate.get("seven_day") if isinstance(rate.get("seven_day"), dict) else None
    if w7 and uc.la_so(w7.get("pct")):
        r7 = w7.get("resets")
        d7 = 0.0 if (uc.la_so(r7) and r7 <= now) else w7["pct"]
        t = "7d usage %g%%" % round(d7, 1)
        tg = uc.phan_tram_tuan_troi(r7, now)
        if tg is not None:
            t += " / %s (%s)" % (s["time"].format(t=tg), s["reset"].format(g=gio(r7)))
            ma = uc.ma_den(d7, tg)
            if d7 >= 95:
                canh.append(s["r7"])
            elif ma in ("Y", "R", "S"):
                canh.append(s[ma])
            t += " · %s %s" % (s["light"], uc.NHAN_DEN[ma])
        phan.append(t)
    fw = uc.fable_that(rate)
    if fw is not None:
        phan.append("%s %g%%" % (s["fable"], round(fw["pct"], 1)))
    elif cache and cache.get("fable_uoc") is not None:
        phan.append("%s ~%d%%" % (s["fable"], cache["fable_uoc"]))
    elif cache and cache.get("fable_ty_le") is not None:
        phan.append("%s %d%%" % (s["fable"], cache["fable_ty_le"]))
    tuoi = int((now - (rate.get("t") or 0)) / 60)
    out = " · ".join(phan) + " · " + s["ago"].format(m=tuoi)
    if tuoi > 30:
        out += s["old"]
    if canh:
        out += " · ! " + "; ".join(canh)
    return dau + out


if __name__ == "__main__":
    try:
        raw = b""
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
        try:
            raw = sys.stdin.buffer.read()  # only the folder fields are used, never the prompt
        except Exception:
            pass
        now = time.time()
        dau = ""
        try:
            data = json.loads(raw.decode("utf-8", errors="replace"))
            dau = uc.tien_to_du_an(*([os.environ.get("CLAUDE_PROJECT_DIR")] + uc.duong_dan_tu_json(data)))
        except Exception:
            dau = uc.tien_to_du_an(os.environ.get("CLAUDE_PROJECT_DIR"))
        print(dong(now, dau))
        uc.lam_moi_nen(now)
    except Exception:
        pass
    sys.exit(0)
