"""usage_chung.py - shared helpers for the usage-tracker skill (Python 3 standard library only).

Paths: the Claude Code config directory is the CLAUDE_CONFIG_DIR variable, default ~/.claude.
The skill's data lives in <config>/usage-tracker/ (rate.json, moc.jsonl, nhip-cache.json).
"""
import datetime
import json
import math
import os
import subprocess
import sys
import time

try:  # Vietnamese message tables; the skill still works (in English) if this file is missing
    import lang_vi
except ImportError:
    lang_vi = None

TUAN_GIAY = 7 * 86400  # seconds in the 7-day window
CUA_SO_CHINH = ("five_hour", "seven_day")  # the two main rate-limit windows


def thu_muc_cau_hinh():
    raw = os.environ.get("CLAUDE_CONFIG_DIR", "").strip().strip('"')
    if raw:
        return os.path.abspath(os.path.expanduser(raw))
    return os.path.join(os.path.expanduser("~"), ".claude")


def thu_muc_du_lieu():
    return os.path.join(thu_muc_cau_hinh(), "usage-tracker")


def ngon_ngu():
    v = os.environ.get("USAGE_TRACKER_LANG", "vi").strip().lower()
    if lang_vi is None:
        return "en"
    return "en" if v.startswith("en") else "vi"


def la_so(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def ra_epoch(v):
    """Number (seconds or milliseconds) or ISO string -> epoch seconds; unreadable -> None."""
    if la_so(v):
        return float(v) / 1000.0 if v > 1e12 else float(v)
    if isinstance(v, str) and 0 < len(v) <= 40:
        try:
            d = datetime.datetime.fromisoformat(v.strip().replace("Z", "+00:00"))
            if d.tzinfo is None:
                d = d.astimezone()
            return d.timestamp()
        except ValueError:
            return None
    return None


def doc_json(duong_dan):
    try:
        with open(duong_dan, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def ghi_tep(duong_dan, noi_dung):
    """Write to a temp file in the same folder, then os.replace. Returns True when done."""
    tam = "%s.%d.tmp" % (duong_dan, os.getpid())
    try:
        os.makedirs(os.path.dirname(duong_dan), exist_ok=True)
        with open(tam, "w", encoding="utf-8", newline="") as f:
            f.write(noi_dung)
        for lan in range(4):
            try:
                os.replace(tam, duong_dan)
                return True
            except OSError:
                time.sleep(0.02 * (lan + 1))
        return False
    except Exception:
        return False
    finally:
        try:
            if os.path.exists(tam):
                os.remove(tam)
        except OSError:
            pass


def cua_so(rl, khoa):
    """Return {'pct': .., 'resets': epoch|None} if the window has a valid used_percentage, else None."""
    w = rl.get(khoa) if isinstance(rl, dict) else None
    if not isinstance(w, dict):
        return None
    pct = w.get("used_percentage")
    if not la_so(pct):
        return None
    return {"pct": float(pct), "resets": ra_epoch(w.get("resets_at"))}


def het_tuan(resets, now):
    """Next weekly reset: roll forward in multiples of 7 days if resets_at is already in the past."""
    if not la_so(resets):
        return None
    while resets <= now:
        resets += TUAN_GIAY
    return resets


def phan_tram_tuan_troi(resets, now):
    """% of the week elapsed = 1 - (resets - now)/604800, clamped to 0..100. None if resets_at is not in the future."""
    if not la_so(resets) or resets <= now:
        return None
    return round(max(0.0, min(1.0, 1 - (resets - now) / float(TUAN_GIAY))) * 100)


def ma_den(pct, tg):
    """Weekly pace light: pct = % used, tg = % of time elapsed. G green / Y yellow / R red / S spare."""
    lech = pct - tg
    if pct >= 95 or lech > 10:
        return "R"
    if lech > 3:
        return "Y"
    if lech < -8:
        return "S"
    return "G"


NHAN_DEN = {
    "vi": lang_vi.NHAN_DEN if lang_vi else None,
    "en": {"G": "GREEN", "Y": "YELLOW", "R": "RED", "S": "SPARE"},
}
NHAN_DEN_ASCII = {
    "vi": {"G": "XANH", "Y": "VANG", "R": "DO", "S": "DU"},
    "en": {"G": "GREEN", "Y": "YELLOW", "R": "RED", "S": "SPARE"},
}


def doc_rate():
    d = doc_json(os.path.join(thu_muc_du_lieu(), "rate.json"))
    return d if isinstance(d, dict) else None


def doc_cache(now):
    c = doc_json(os.path.join(thu_muc_du_lieu(), "nhip-cache.json"))
    if not isinstance(c, dict):
        return None
    het = c.get("het")
    if la_so(het) and het < now:  # cache from a previous week
        return None
    return c


def _pct_hien(w, now):
    """Displayed % of one window; a window that has already reset (resets_at in the past) -> 0."""
    if not w:
        return None
    r = w.get("resets")
    if la_so(r) and r <= now:
        return 0.0
    return w.get("pct")


def fable_that(rate):
    """The per-model window whose key contains 'fable' (if Claude Code sends one)."""
    khac = (rate or {}).get("khac")
    if isinstance(khac, dict):
        for k, w in khac.items():
            if "fable" in str(k).lower() and isinstance(w, dict) and la_so(w.get("pct")):
                return w
    return None


def lam_moi_nen(now):
    """If the pace cache is older than 60 minutes (or missing): run nhip_tuan.py --im in the background, without waiting. 120 s lock."""
    try:
        if os.environ.get("USAGE_TRACKER_NO_REFRESH"):  # for tests only
            return
        dl = thu_muc_du_lieu()
        c = doc_json(os.path.join(dl, "nhip-cache.json"))
        if isinstance(c, dict) and la_so(c.get("t")) and now - c["t"] < 3600:
            return
        khoa = os.path.join(dl, "lam-moi.lock")
        if os.path.exists(khoa) and now - os.path.getmtime(khoa) < 120:
            return
        os.makedirs(dl, exist_ok=True)
        with open(khoa, "w") as f:
            f.write(str(int(now)))
        kich_ban = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nhip_tuan.py")
        kw = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
              "close_fds": True}
        if os.name == "nt":
            kw["creationflags"] = 0x00000008 | 0x08000000
        else:
            kw["start_new_session"] = True
        subprocess.Popen([sys.executable, kich_ban, "--im"], **kw)
    except Exception:
        pass


def dong_ngan(rate, cache, now):
    """Status-line text (ASCII): Usage 5h X% | Fable Z% | 7d usage Y% | 7d time T% | LIGHT (Fable comes before 7d)"""
    ng = ngon_ngu()
    h5 = _pct_hien((rate or {}).get("five_hour"), now)
    d7w = (rate or {}).get("seven_day")
    d7 = _pct_hien(d7w, now)

    def p(v):
        return ("%g%%" % round(v, 1)) if v is not None else "-"

    out = "Usage 5h %s" % p(h5)
    fw = fable_that(rate)
    if fw is not None:
        out += " | Fable %s" % p(_pct_hien(fw, now))
    elif cache and cache.get("fable_uoc") is not None:
        out += " | Fable ~%d%%" % cache["fable_uoc"]
    elif cache and cache.get("fable_ty_le") is not None:
        out += " | Fable %d%% %s" % (cache["fable_ty_le"], "tong" if ng == "vi" else "of total")
    out += " | 7d usage %s" % p(d7)
    tg = phan_tram_tuan_troi((d7w or {}).get("resets"), now)
    if tg is not None:
        out += " | 7d time %d%%" % tg
        if d7 is not None:
            out += " | %s" % NHAN_DEN_ASCII[ng][ma_den(d7, tg)]
    return out
