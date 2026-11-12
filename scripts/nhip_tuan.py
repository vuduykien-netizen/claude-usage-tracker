#!/usr/bin/env python3
"""nhip_tuan.py - nhip han muc tuan + ty le Fable tu transcript Claude Code. Chi doc tep, khong goi mang.

Dung:
  python3 nhip_tuan.py                      in nhip tuan (da dung % so voi % thoi gian, den) + phan Fable
  python3 nhip_tuan.py --moc 73 47          ghi mot moc ban doc o /usage: tuan (moi model) 73%, tuan Fable 47%
  python3 nhip_tuan.py --moc 73             chi moc tuan
  python3 nhip_tuan.py --moc 73 47 --luc "2026-01-15 13:05"   moc ghi cho gio local cu the
  python3 nhip_tuan.py --im                 chay im (chi cap nhat bo dem, do hook/thanh trang thai goi o nen)
  USAGE_TRACKER_LANG=en                     in tieng Anh

Cua so tuan lay tu seven_day.resets_at (do statusline_usage.py ghi). Chua co: tuan tinh tu 00:00 thu Hai
gan nhat theo gio may va ghi ro la uoc.
Chi doc 3 truong cua transcript: model, usage, timestamp (khong doc noi dung hoi thoai).
"quy doi" = vao moi x1 + ghi cache x1,25 + doc cache x0,1 + output x5 (uoc luong).
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

CH = {
    "vi": {
        "tuan": "Tuần từ {a} · đã qua {gio:.0f}/168 giờ = {tg:.0f}% thời gian ({nguon})",
        "that": "Đã dùng {u:.0f}% (số thật từ thanh trạng thái, cách {tuoi} phút) · lệch {l:+.0f} điểm · đèn {den}",
        "uoc": "Ước đã dùng {u:.0f}% (từ mốc {luc} = {m:.0f}% + quy đổi phát sinh) · lệch {l:+.0f} điểm · đèn {den}",
        "none": "Chưa có số tuần: cài thanh trạng thái (install.py) hoặc ghi mốc: nhip_tuan.py --moc <tuần%> [fable%]",
        "fthat": "Fable: {p:.0f}% (hạn mức riêng theo model do Claude Code gửi)",
        "fuoc": "Fable: ước {p:.0f}% tuần Fable (mốc {luc} = {m:.0f}%) · quy đổi {q:,.0f} nghìn, {r:.0f}% tổng",
        "fty": "Fable: {q:,.0f} nghìn quy đổi = {r:.0f}% lượng dùng tuần; chưa có mốc % Fable (đọc /usage rồi: nhip_tuan.py --moc <tuần%> <fable%>)",
        "fkhong": "Fable: tuần này chưa thấy lượt dùng model Fable trong transcript",
        "moc": "Đã ghi mốc",
        "sai": "Số phải trong 0..100",
        "est": "ước theo giờ máy, chưa có resets_at",
        "rl": "theo seven_day.resets_at",
    },
    "en": {
        "tuan": "Week from {a} · {gio:.0f}/168 hours elapsed = {tg:.0f}% of time ({nguon})",
        "that": "Used {u:.0f}% (real number from the status line, {tuoi} min old) · gap {l:+.0f} pts · light {den}",
        "uoc": "Estimated used {u:.0f}% (from marker {luc} = {m:.0f}% + usage since) · gap {l:+.0f} pts · light {den}",
        "none": "No weekly number yet: install the status line (install.py) or log a marker: nhip_tuan.py --moc <week%> [fable%]",
        "fthat": "Fable: {p:.0f}% (per-model limit sent by Claude Code)",
        "fuoc": "Fable: est. {p:.0f}% of the Fable week (marker {luc} = {m:.0f}%) · {q:,.0f}k weighted, {r:.0f}% of total",
        "fty": "Fable: {q:,.0f}k weighted = {r:.0f}% of this week's usage; no Fable % marker yet (read /usage, then: nhip_tuan.py --moc <week%> <fable%>)",
        "fkhong": "Fable: no Fable-model usage found in transcripts this week",
        "moc": "Marker saved",
        "sai": "Numbers must be within 0..100",
        "est": "estimated from machine clock, no resets_at yet",
        "rl": "from seven_day.resets_at",
    },
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
    """Danh sach (epoch, la_fable, [4 so usage]); khu trung theo message id."""
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
    ng = uc.ngon_ngu()
    s = CH[ng]
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

    # cua so tuan
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

    # % tuan: so that (rate.json ghi trong tuan nay) > moc + quy doi
    uoc, dong1 = None, s["none"]
    if d7 and uc.la_so(d7.get("pct")) and uc.la_so(rate.get("t")) and rate["t"] >= bat_dau:
        uoc = float(d7["pct"])
        l = uoc - tg
        dong1 = s["that"].format(u=uoc, tuoi=int((now - rate["t"]) / 60), l=l, den=uc.NHAN_DEN[ng][uc.ma_den(uoc, tg)])
    elif mocs and quy_doi(rows, mocs[-1]["t"]) > 0 and mocs[-1]["tuan"] > 0:
        m = mocs[-1]
        mot = quy_doi(rows, m["t"]) / m["tuan"]
        uoc = m["tuan"] + (Q - quy_doi(rows, m["t"])) / mot
        dong1 = s["uoc"].format(u=uoc, luc=m["luc"], m=m["tuan"], l=uoc - tg, den=uc.NHAN_DEN[ng][uc.ma_den(uoc, tg)])

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
