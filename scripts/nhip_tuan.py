#!/usr/bin/env python3
"""nhip_tuan.py - weekly pace + Fable share from Claude Code transcripts. Reads files only, no network.

Usage:
  python3 nhip_tuan.py                      print the weekly pace (% used vs % of time elapsed, light) + the Fable part
  python3 nhip_tuan.py --moc 73 47          log a marker you read in /usage: week (all models) 73%, Fable week 47%
  python3 nhip_tuan.py --moc 73             week marker only
  python3 nhip_tuan.py --moc 73 47 --luc "2026-01-15 13:05"   marker for a specific local time
  python3 nhip_tuan.py --im                 run silently (only refreshes the cache; called in the background by the hook/status line)

The week window comes from seven_day.resets_at (written by statusline_usage.py). If it is missing, the week is
counted from the most recent Monday 00:00 by the machine clock and the output says it is an estimate.
Reads only 3 transcript fields: model, usage, timestamp (never conversation content).
"weighted" = fresh input x1 + cache write x1.25 + cache read x0.1 + output x5 (an estimate).
"""
import datetime
import glob
import json
import os
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import usage_chung as uc  # noqa: E402

KS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
W = (1.0, 1.25, 0.1, 5.0)

S = {
    "tuan": "Week from {a} · {gio:.0f}/168 hours elapsed = {tg:.0f}% of time ({nguon})",
    "that": "Used {u:.0f}% (real number from the status line, {tuoi} min old) · gap {l:+.0f} pts · light {den}",
    "uoc": "Estimated used {u:.0f}% (from marker {luc} = {m:.0f}% + usage since) · gap {l:+.0f} pts · light {den}",
    "none": "No weekly number yet: install the status line (install.py) or log a marker: nhip_tuan.py --moc <week%> [fable%]",
    "fthat": "7d Fable usage: {p:.0f}% (per-model limit sent by Claude Code)",
    "fuoc": "7d Fable usage: est. {p:.0f}% (marker {luc} = {m:.0f}%) · {q:,.0f}k weighted, {r:.0f}% of total usage",
    "fty": "7d Fable usage: {q:,.0f}k weighted = {r:.0f}% of this week's usage; no Fable % marker yet (read /usage, then: nhip_tuan.py --moc <week%> <fable%>)",
    "fkhong": "7d Fable usage: no Fable-model usage found in transcripts this week",
    "moc": "Marker saved",
    "sai": "Numbers must be within 0..100",
    "est": "estimated from machine clock, no resets_at yet",
    "rl": "from seven_day.resets_at",
}


def tham_so(ten):
    a = sys.argv[1:]
    if ten in a:
        i = a.index(ten)
        return a[i + 1] if i + 1 < len(a) else None
    return None


def doc_moc(tep, tu):
    ds = []
    try:
        with open(tep, encoding="utf-8") as f:
            for l in f:
                try:
                    d = json.loads(l)
                    if uc.la_so(d.get("t")) and uc.la_so(d.get("tuan")) and d["t"] >= tu:
                        ds.append(d)
                except Exception:
                    pass
    except OSError:
        pass
    ds.sort(key=lambda d: d["t"])
    return ds


def doc_transcript(thu_muc_cau_hinh, tu):
    """List of (epoch, is_fable, [4 usage numbers]); de-duplicated by message id."""
    thay, rows = {}, []
    mau = os.path.join(thu_muc_cau_hinh, "projects", "**", "*.jsonl")
    for f in glob.glob(mau, recursive=True):
        try:
            if os.path.getmtime(f) < tu:
                continue
            fh = open(f, encoding="utf-8", errors="ignore")
        except OSError:
            continue
        with fh:
            for line in fh:
                if '"usage"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                if not isinstance(o, dict) or o.get("type") != "assistant":
                    continue
                msg = o.get("message") or {}
                u = msg.get("usage")
                if not isinstance(u, dict) or msg.get("model") == "<synthetic>":
                    continue
                us = [u.get(k) if uc.la_so(u.get(k)) else 0 for k in KS]
                mid = msg.get("id") or o.get("uuid")
                if mid in thay:
                    if us[3] > thay[mid][3]:
                        thay[mid][3] = us[3]
                    continue
                t = uc.ra_epoch(o.get("timestamp"))
                if t is None or t < tu:
                    continue
                thay[mid] = us
                rows.append((t, "fable" in str(msg.get("model") or "").lower(), us))
    return rows


def quy_doi(rows, den=None, chi_fable=False):
    return sum(sum(a * b for a, b in zip(us, W)) for t, fb, us in rows
               if (den is None or t <= den) and (fb or not chi_fable))


def chay():
    s = S
    now = time.time()
    dl = uc.thu_muc_du_lieu()
    tep_moc = os.path.join(dl, "moc.jsonl")
    im = "--im" in sys.argv[1:]

    if "--moc" in sys.argv[1:]:
        a = sys.argv[sys.argv.index("--moc") + 1:]
        try:
            tuan = float(a[0])
            fable = float(a[1]) if len(a) > 1 and not a[1].startswith("--") else None
            for v in (tuan, fable):
                if v is not None and not (0 <= v <= 100):
                    raise ValueError
        except (ValueError, IndexError):
            print(s["sai"])
            sys.exit(2)
        luc = tham_so("--luc")
        try:
            t = datetime.datetime.strptime(luc, "%Y-%m-%d %H:%M").timestamp() if luc else now
        except ValueError:
            print("--luc: YYYY-MM-DD HH:MM")
            sys.exit(2)
        d = {"luc": datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M"), "t": t, "tuan": tuan, "fable": fable}
        os.makedirs(dl, exist_ok=True)
        with open(tep_moc, "a", encoding="utf-8", newline="") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
        print(s["moc"], d)

    # week window
    rate = uc.doc_rate() or {}
    d7 = rate.get("seven_day") if isinstance(rate.get("seven_day"), dict) else None
    het = uc.het_tuan(d7.get("resets"), now) if d7 else None
    if het is not None:
        bat_dau, nguon = het - uc.TUAN_GIAY, s["rl"]
    else:
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        bat_dau = (today - datetime.timedelta(days=today.weekday())).timestamp()
        het, nguon = bat_dau + uc.TUAN_GIAY, s["est"]
    gio = (now - bat_dau) / 3600.0
    tg = max(0.0, min(100.0, gio * 100 / 168))

    rows = doc_transcript(uc.thu_muc_cau_hinh(), bat_dau)
    Q = quy_doi(rows)
    QF = quy_doi(rows, None, True)
    ty_le = round(QF * 100 / Q) if Q > 0 else None
    mocs = doc_moc(tep_moc, bat_dau)

    # week %: real number (rate.json written this week) > marker + weighted usage since
    uoc, dong1 = None, s["none"]
    if d7 and uc.la_so(d7.get("pct")) and uc.la_so(rate.get("t")) and rate["t"] >= bat_dau:
        uoc = float(d7["pct"])
        l = uoc - tg
        dong1 = s["that"].format(u=uoc, tuoi=int((now - rate["t"]) / 60), l=l, den=uc.NHAN_DEN[uc.ma_den(uoc, tg)])
    elif mocs and quy_doi(rows, mocs[-1]["t"]) > 0 and mocs[-1]["tuan"] > 0:
        m = mocs[-1]
        mot = quy_doi(rows, m["t"]) / m["tuan"]
        uoc = m["tuan"] + (Q - quy_doi(rows, m["t"])) / mot
        dong1 = s["uoc"].format(u=uoc, luc=m["luc"], m=m["tuan"], l=uoc - tg, den=uc.NHAN_DEN[uc.ma_den(uoc, tg)])

    # Fable
    fw = uc.fable_that(rate)
    fuoc = None
    mf = [m for m in mocs if m.get("fable")]
    if fw is not None:
        dong2 = s["fthat"].format(p=fw["pct"])
    elif mf and quy_doi(rows, mf[-1]["t"], True) > 0:
        m = mf[-1]
        qf = quy_doi(rows, m["t"], True)
        fuoc = m["fable"] + (QF - qf) / (qf / m["fable"])
        dong2 = s["fuoc"].format(p=fuoc, luc=m["luc"], m=m["fable"], q=QF / 1e3, r=ty_le or 0)
    elif QF > 0:
        dong2 = s["fty"].format(q=QF / 1e3, r=ty_le or 0)
    else:
        dong2 = s["fkhong"]

    cache = {
        "t": now, "het": het, "bat_dau": bat_dau, "thoi_gian": round(tg),
        "uoc": None if uoc is None else round(uoc),
        "den": None if uoc is None else uc.ma_den(uoc, tg),
        "fable_uoc": None if fuoc is None else round(fuoc),
        "fable_ty_le": ty_le,
        "quy_doi": round(Q), "quy_doi_fable": round(QF),
    }
    uc.ghi_tep(os.path.join(dl, "nhip-cache.json"), json.dumps(cache, ensure_ascii=True))
    if im:
        return
    print(s["tuan"].format(a=datetime.datetime.fromtimestamp(bat_dau).strftime("%d/%m %H:%M"), gio=gio, tg=tg, nguon=nguon))
    print(dong1)
    print(dong2)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        chay()
    except SystemExit:
        raise
    except Exception as e:
        if "--im" not in sys.argv[1:]:
            print("nhip_tuan: %s" % type(e).__name__)
    sys.exit(0)
