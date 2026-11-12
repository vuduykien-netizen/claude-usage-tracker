#!/usr/bin/env python3
"""hook_usage.py - hook UserPromptSubmit cua Claude Code: in MOT dong nhac usage moi luot.

Doc <cau hinh>/usage-tracker/rate.json (do statusline_usage.py ghi) va nhip-cache.json (do nhip_tuan.py ghi).
Stdout cua hook nay duoc Claude Code them vao ngu canh luot do. Khong doc noi dung lenh cua ban.
Bo dem nhip cu > 60 phut thi chay nhip_tuan.py o nen (khong cho). Luon thoat 0, khong nem loi.
USAGE_TRACKER_LANG=en de in tieng Anh.
"""
import os
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usage_chung as uc  # noqa: E402

CH = {
    "vi": {
        "none": "usage: chưa có số (thanh trạng thái chưa ghi lần nào)",
        "ago": "số cách {m} phút", "old": " (CŨ)", "time": "tuần đã trôi {t}%", "reset": "reset {g}",
        "r5": "5h ≥90%: nên chốt việc đang làm, không mở việc mới",
        "r5b": "5h ≥75%: dùng model nhẹ, gom việc",
        "r7": "7d ≥95%: chỉ việc gấp",
        "Y": "7d đi nhanh hơn lịch: giảm việc song song, dùng model nhẹ",
        "R": "7d vượt lịch nhiều: chỉ việc có hạn",
        "S": "7d còn dư: có thể xả việc xếp hàng",
        "light": "đèn", "fable": "Fable", "tong": "{r}% lượng dùng tuần",
    },
    "en": {
        "none": "usage: no number yet (status line has not written any)",
        "ago": "{m} min old", "old": " (STALE)", "time": "week {t}% elapsed", "reset": "reset {g}",
        "r5": "5h >=90%: wrap up current work, do not start new work",
        "r5b": "5h >=75%: use lighter models, batch work",
        "r7": "7d >=95%: urgent work only",
        "Y": "7d is ahead of schedule: fewer parallel tasks, lighter models",
        "R": "7d is far ahead of schedule: deadline work only",
        "S": "7d has headroom: good time for queued work",
        "light": "light", "fable": "Fable", "tong": "{r}% of this week's usage",
    },
}


def gio(ts):
    return time.strftime("%H:%M %d/%m", time.localtime(ts))


def dong(now):
    ng = uc.ngon_ngu()
    s = CH[ng]
    rate = uc.doc_rate()
    if not rate:
        return s["none"]
    cache = uc.doc_cache(now)
    phan, canh = [], []
    w5 = rate.get("five_hour") if isinstance(rate.get("five_hour"), dict) else None
    if w5 and uc.la_so(w5.get("pct")):
        h5 = 0.0 if (uc.la_so(w5.get("resets")) and w5["resets"] <= now) else w5["pct"]
        t = "5h %g%%" % round(h5, 1)
        if h5 and uc.la_so(w5.get("resets")):
            t += " (%s)" % s["reset"].format(g=gio(w5["resets"]))
        phan.append(t)
        if h5 >= 90:
            canh.append(s["r5"])
        elif h5 >= 75:
            canh.append(s["r5b"])
    w7 = rate.get("seven_day") if isinstance(rate.get("seven_day"), dict) else None
    if w7 and uc.la_so(w7.get("pct")):
        r7 = w7.get("resets")
        d7 = 0.0 if (uc.la_so(r7) and r7 <= now) else w7["pct"]
        t = "7d %g%%" % round(d7, 1)
        tg = uc.phan_tram_tuan_troi(r7, now)
        if tg is not None:
            t += " / %s (%s)" % (s["time"].format(t=tg), s["reset"].format(g=gio(r7)))
            ma = uc.ma_den(d7, tg)
            if d7 >= 95:
                canh.append(s["r7"])
            elif ma in ("Y", "R", "S"):
                canh.append(s[ma])
            t += " · %s %s" % (s["light"], uc.NHAN_DEN[ng][ma])
        phan.append(t)
    fw = uc.fable_that(rate)
    if fw is not None:
        phan.append("%s %g%%" % (s["fable"], round(fw["pct"], 1)))
    elif cache and cache.get("fable_uoc") is not None:
        phan.append("%s ~%d%%" % (s["fable"], cache["fable_uoc"]))
    elif cache and cache.get("fable_ty_le") is not None:
        phan.append("%s %s" % (s["fable"], s["tong"].format(r=cache["fable_ty_le"])))
    tuoi = int((now - (rate.get("t") or 0)) / 60)
    out = "usage " + " · ".join(phan) + " · " + s["ago"].format(m=tuoi)
    if tuoi > 30:
        out += s["old"]
    if canh:
        out += " · ! " + "; ".join(canh)
    return out


if __name__ == "__main__":
    try:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
        try:
            sys.stdin.buffer.read()  # bo qua noi dung hook gui vao
        except Exception:
            pass
        now = time.time()
        print(dong(now))
        uc.lam_moi_nen(now)
    except Exception:
        pass
    sys.exit(0)
