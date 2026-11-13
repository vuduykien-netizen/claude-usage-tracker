#!/usr/bin/env python3
"""kiem_thu.py - automated test suite for the usage-tracker skill. Uses only a temp directory, never touches the real ~/.claude.

  python3 tests/kiem_thu.py [--tmp <dir>]   run the cases, print PASS/FAIL + a TOTAL line
  python3 tests/kiem_thu.py --pha            set deliberately WRONG expectations: every case must FAIL ("caught N/total")

The default (Vietnamese) locale is exercised on purpose; its expected strings are written as @XXXX
code points (see vi()) so this file stays English-only.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SC = os.path.join(GOC, "scripts")
PHA = "--pha" in sys.argv[1:]
KQ = []


def chay(script, cfg, stdin="", args=(), env_them=None):
    env = dict(os.environ)
    env.update({"CLAUDE_CONFIG_DIR": cfg, "USAGE_TRACKER_NO_REFRESH": "1", "PYTHONUTF8": "1",
                "USAGE_TRACKER_LANG": "vi"})
    env.update(env_them or {})
    p = subprocess.run([sys.executable, script] + list(args), input=stdin.encode("utf-8"),
                       capture_output=True, env=env, timeout=60)
    return p.returncode, p.stdout.decode("utf-8", "replace").strip(), p.stderr.decode("utf-8", "replace").strip()


def vi(s):
    """Decode '@01b0' style code points, so the expected Vietnamese output can be written in ASCII."""
    return re.sub(r"@([0-9a-f]{4})", lambda m: chr(int(m.group(1), 16)), s)


def kiem(ten, thuc, mong):
    if PHA:
        mong = "@@DELIBERATELY-WRONG@@"
    ok = thuc == mong
    KQ.append((ten, ok))
    print("%s  %s" % ("PASS " if ok else "FAIL ", ten))
    if not ok and not PHA:
        print("      actual:   %r\n      expected: %r" % (thuc, mong))


def doc(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def iso(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).isoformat()


def stdin_rl(h5=None, d7=None, **khac):
    now = time.time()
    rl = {}
    if h5 is not None:
        rl["five_hour"] = {"used_percentage": h5, "resets_at": now + 3600}
    if d7 is not None:
        rl["seven_day"] = {"used_percentage": d7, "resets_at": now + 302400}  # week is exactly 50% elapsed
    for k, v in khac.items():
        rl[k] = {"used_percentage": v, "resets_at": now + 302400}
    return json.dumps({"rate_limits": rl, "model": {"id": "x"}})


def dong_tu(cfg, **kw):
    return chay(os.path.join(SC, "statusline_usage.py"), cfg, stdin_rl(**kw))


def ghi_transcript(cfg, dong):
    d = os.path.join(cfg, "projects", "p1")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "s.jsonl"), "w", encoding="utf-8") as f:
        for o in dong:
            f.write(json.dumps(o) + "\n")


def tn(t, mid, model, i, o, loai="assistant"):
    return {"type": loai, "timestamp": iso(t), "uuid": "u" + mid, "message": {
        "id": mid, "model": model, "content": "FAKE CONTENT THAT MUST NOT BE READ",
        "usage": {"input_tokens": i, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": o}}}


def main():
    goc_tam = tham_tmp()
    now = time.time()

    # 1) full 5h + 7d
    c1 = os.path.join(goc_tam, "c1")
    rc, out, _ = dong_tu(c1, h5=23.5, d7=64)
    kiem("1 full 5h+7d: line", out, "Usage 5h 23.5% | 7d usage 64% | 7d time 50% | DO")
    kiem("1 exit 0", rc, 0)
    r = doc(os.path.join(c1, "usage-tracker", "rate.json"))
    kiem("1 rate.json: 5h + 7d", (r["five_hour"]["pct"], r["seven_day"]["pct"]), (23.5, 64.0))

    # 2) 7d only (+ resets_at as an ISO string)
    c2 = os.path.join(goc_tam, "c2")
    iso7 = iso(now + 302400)
    rc, out, _ = chay(os.path.join(SC, "statusline_usage.py"), c2,
                      json.dumps({"rate_limits": {"seven_day": {"used_percentage": 50, "resets_at": iso7}}}))
    kiem("2 7d only: line", out, "Usage 5h - | 7d usage 50% | 7d time 50% | XANH")
    kiem("2 rate.json five_hour = null", doc(os.path.join(c2, "usage-tracker", "rate.json"))["five_hour"], None)

    # 3) separate per-model key
    c3 = os.path.join(goc_tam, "c3")
    rc, out, _ = dong_tu(c3, h5=10, d7=64, seven_day_fable=12)
    kiem("3 separate Fable key: line", out, "Usage 5h 10% | Fable 12% | 7d usage 64% | 7d time 50% | DO")

    # 4) transcript with Fable -> share
    c4 = os.path.join(goc_tam, "c4")
    dong_tu(c4, h5=23.5, d7=64)
    ghi_transcript(c4, [
        tn(now - 3 * 86400, "A", "claude-fable-x", 1000, 200),
        tn(now - 3 * 86400, "A", "claude-fable-x", 1000, 50),      # duplicate id, smaller output: dropped
        tn(now - 2 * 86400, "B", "claude-sonnet-x", 3000, 400),
        tn(now - 2 * 86400, "S", "<synthetic>", 99999, 99999),       # dropped
        tn(now - 6 * 86400, "OLD", "claude-fable-x", 99999, 0),      # before the start of the week (7d - 3.5d): dropped
        {"type": "user", "timestamp": iso(now - 86400), "message": {"id": "U", "usage": {"input_tokens": 99999}}},
    ])
    rc, out, _ = chay(os.path.join(SC, "nhip_tuan.py"), c4, args=["--im"])
    ca = doc(os.path.join(c4, "usage-tracker", "nhip-cache.json"))
    kiem("4 Fable share = 2000/7000", ca["fable_ty_le"], 29)
    kiem("4 weighted total / Fable", (ca["quy_doi"], ca["quy_doi_fable"]), (7000, 2000))
    rc, out, _ = dong_tu(c4, h5=23.5, d7=64)
    kiem("4 status line shows the Fable share", out,
         "Usage 5h 23.5% | Fable 29% tong | 7d usage 64% | 7d time 50% | DO")

    # 5) /usage marker -> Fable % estimate
    c5 = os.path.join(goc_tam, "c5")
    dong_tu(c5, h5=1, d7=64)
    ghi_transcript(c5, [
        tn(now - 3 * 86400, "A", "claude-fable-x", 1000, 200),
        tn(now - 600, "C", "claude-fable-x", 1000, 200),
        tn(now - 2 * 86400, "B", "claude-sonnet-x", 3000, 400),
    ])
    luc = datetime.datetime.fromtimestamp(now - 1800).strftime("%Y-%m-%d %H:%M")
    chay(os.path.join(SC, "nhip_tuan.py"), c5, args=["--moc", "50", "10", "--luc", luc, "--im"])
    rc, out, _ = chay(os.path.join(SC, "nhip_tuan.py"), c5)
    ca = doc(os.path.join(c5, "usage-tracker", "nhip-cache.json"))
    kiem("5 Fable estimate 20% (marker 10% + usage since)", ca["fable_uoc"], 20)
    kiem("5 output has the Fable estimate line", vi("Fable: @01b0@1edbc 20%") in out, True)
    kiem("5 marker outside 0..100 is rejected (code 2)", chay(os.path.join(SC, "nhip_tuan.py"), c5, args=["--moc", "150"])[0], 2)

    # 6) broken stdin does not overwrite
    p6 = os.path.join(c1, "usage-tracker", "rate.json")
    truoc = open(p6, "rb").read()
    rc, out, _ = chay(os.path.join(SC, "statusline_usage.py"), c1, "not json {{")
    kiem("6 broken JSON: prints 'Usage -', exit 0", (rc, out), (0, "Usage -"))
    kiem("6 broken JSON: old file not overwritten", open(p6, "rb").read() == truoc, True)

    # 7) hook
    rc, out, _ = chay(os.path.join(SC, "hook_usage.py"), c1, "{}")
    kiem("7 hook: exit 0, one line, has the numbers",
         (rc, out.count("\n"), "5h 23.5%" in out, "7d 64%" in out and vi("@0111@00e8n @0110@1ece") in out),
         (0, 0, True, True))
    kiem("7 hook en", "light RED" in chay(os.path.join(SC, "hook_usage.py"), c1, "{}", env_them={"USAGE_TRACKER_LANG": "en"})[1], True)
    kiem("7 hook with no data", chay(os.path.join(SC, "hook_usage.py"), os.path.join(goc_tam, "trong"), "")[1][:11],
         vi("usage: ch@01b0a"))

    # 8) install on fake settings
    c8 = os.path.join(goc_tam, "c8")
    os.makedirs(c8)
    goc = {"model": "fake", "permissions": {"allow": ["Bash(ls)"]}, "statusLine": {"type": "command", "command": "mine"},
           "hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "echo old"}]}],
                     "Stop": [{"hooks": [{"type": "command", "command": "echo stop"}]}]}}
    sp = os.path.join(c8, "settings.json")
    json.dump(goc, open(sp, "w", encoding="utf-8"))
    ins = os.path.join(GOC, "install.py")
    rc, out, _ = chay(ins, c8, args=["--dry-run"])
    kiem("8 dry-run writes nothing", doc(sp) == goc, True)
    rc, out, _ = chay(ins, c8)
    s = doc(sp)
    kiem("8 keeps model/permissions/Stop/existing statusLine", (s["model"], s["permissions"], s["hooks"]["Stop"], s["statusLine"]),
         ("fake", goc["permissions"], goc["hooks"]["Stop"], {"type": "command", "command": "mine"}))
    ds = s["hooks"]["UserPromptSubmit"]
    kiem("8 existing hook intact + one group added", (len(ds), ds[0]), (2, goc["hooks"]["UserPromptSubmit"][0]))
    kiem("8 prints how to chain the statusLine", "ALREADY HAVE" in out and "--quiet" in out, True)
    kiem("8 backup exists", len([f for f in os.listdir(c8) if f.endswith(".bak")]), 1)
    chay(ins, c8)
    kiem("8 running again adds no duplicate", len(doc(sp)["hooks"]["UserPromptSubmit"]), 2)
    kiem("8 bin files copied", sorted(os.listdir(os.path.join(c8, "usage-tracker", "bin"))),
         sorted(["usage_chung.py", "lang_vi.py", "statusline_usage.py", "nhip_tuan.py", "hook_usage.py"]))
    # settings without a statusLine
    c9 = os.path.join(goc_tam, "c9")
    os.makedirs(c9)
    json.dump({"env": {"A": "1"}}, open(os.path.join(c9, "settings.json"), "w", encoding="utf-8"))
    chay(ins, c9)
    s9 = doc(os.path.join(c9, "settings.json"))
    kiem("9 no statusLine yet: set + keep env", ("statusline_usage.py" in s9["statusLine"]["command"], s9["env"]), (True, {"A": "1"}))
    # run the installed status line to make sure the command works
    cmd = s9["statusLine"]["command"]
    p = subprocess.run(cmd.strip('"').split('" "'), input=stdin_rl(h5=5, d7=50).encode(), capture_output=True, timeout=60,
                       env=dict(os.environ, CLAUDE_CONFIG_DIR=c9, USAGE_TRACKER_NO_REFRESH="1"))
    kiem("9 the installed statusLine command runs", p.stdout.decode().strip(), "Usage 5h 5% | 7d usage 50% | 7d time 50% | XANH")
    # uninstall
    chay(ins, c9, args=["--uninstall"])
    s9 = doc(os.path.join(c9, "settings.json"))
    kiem("9 uninstall: only env left, data kept", (s9, os.path.exists(os.path.join(c9, "usage-tracker", "rate.json"))),
         ({"env": {"A": "1"}}, True))
    chay(ins, c8, args=["--uninstall"])
    s8 = doc(sp)
    kiem("8 uninstall: back to the original settings (the user's statusLine/hook remain)", s8, goc)
    # broken settings
    c10 = os.path.join(goc_tam, "c10")
    os.makedirs(c10)
    open(os.path.join(c10, "settings.json"), "w").write("{broken")
    rc, out, _ = chay(ins, c10)
    kiem("10 broken settings: stop, write nothing", (rc, open(os.path.join(c10, "settings.json")).read()), (2, "{broken"))

    dat = sum(1 for _, o in KQ if o)
    if PHA:
        print("TOTAL deliberately-wrong run: caught %d/%d cases" % (len(KQ) - dat, len(KQ)))
        return 0 if dat == 0 else 1
    print("TOTAL: %d/%d passed" % (dat, len(KQ)))
    return 0 if dat == len(KQ) else 1


def tham_tmp():
    a = sys.argv[1:]
    if "--tmp" in a:
        d = a[a.index("--tmp") + 1]
        os.makedirs(d, exist_ok=True)
        return os.path.abspath(d)
    return tempfile.mkdtemp(prefix="usage-tracker-test-")


if __name__ == "__main__":
    sys.exit(main())
