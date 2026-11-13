---
name: theo-doi-usage
description: Track Claude Code usage limits on the status line, plus a one-line reminder each turn: 5-hour %, 7-day % (real numbers from rate_limits), % of the week elapsed, a weekly pace light (GREEN/YELLOW/RED/SPARE), and the Fable share (Fable's share of the week's usage, a Fable % estimated from a /usage marker, or a per-model limit if Claude Code sends one). Use when asked about "usage", "rate limit", "how much of my week is left", "how much of my 5-hour limit is used", "how much Fable have I used", "install the usage status line", or "log a /usage marker". Not for changing plans, buying extra capacity or reading conversation content.
---

# Usage tracker

## 1. What it does
The status line shows one line, in a fixed order:

`Usage 5h 23% | Fable 17% of total | 7d usage 56% | 7d time 48% | YELLOW`

(With the default language the last label reads `VANG` and `of total` reads `tong`; see section 6.)

- `5h` / `7d usage`: percent used, the real numbers Claude Code passes to the status line (`rate_limits.five_hour`, `rate_limits.seven_day`). A missing window shows `-`.
- `7d time`: percent of the week elapsed = 1 - (`seven_day.resets_at` - now) / 7 days. The weekly reset time comes from `resets_at`, never a hard-coded hour.
- The light compares `7d usage` with `7d time`: more than 10 points ahead or 95% and above = RED, more than 3 ahead = YELLOW, more than 8 behind = SPARE, otherwise GREEN.
- `Fable`: (a) `Fable 17%` if Claude Code sends a separate limit key containing "fable"; (b) `Fable ~17%` estimated from a `/usage` marker you logged; (c) `Fable 17% of total` = Fable's share of this week's usage, computed from the transcripts. With no Fable turns the field is omitted.
- The `UserPromptSubmit` hook adds one reminder line per turn (with a hint to lighten the load when the light is YELLOW/RED or 5h is at 75% or more).

## 2. When the user asks (steps)
1. "How much is left?" / "How much Fable have I used?": run `python3 <skill folder>/scripts/nhip_tuan.py` (or the installed copy in `<config>/usage-tracker/bin/`) and read the result to the user in plain words. If there is no number yet, tell the user to install (section 3) and send one message so the status line records numbers.
2. The user wants a closer Fable %: ask them to open `/usage`, read the two numbers "week (all models)" and "week Fable", then run `nhip_tuan.py --moc <week%> <fable%>`.
3. Not installed: run `python3 <skill folder>/install.py --dry-run`, show it to the user, then run `install.py` once they agree.

## 3. Install / uninstall
`python3 install.py` backs up `settings.json`, copies the scripts to `<config>/usage-tracker/bin/`, adds a `statusLine` (if none exists) and one `UserPromptSubmit` hook group. If another status line exists it is not overwritten; the installer prints how to chain it (`statusline_usage.py --quiet`). Uninstall: `python3 install.py --uninstall`. Details are in `README.md`.

## 4. Stop points
- Do not edit `settings.json` by hand or with any command other than `install.py` (it backs up first and asks before touching what already exists).
- Never overwrite the user's existing status line or hooks. If they want a full replacement, let them edit it themselves.
- Never delete the config directory; uninstall removes only the entries and files the skill created.

## 5. Privacy
Reads only three transcript fields, `model`, `usage` and `timestamp`, never conversation content. No network calls. Data lives in `<config>/usage-tracker/`; `<config>` = `CLAUDE_CONFIG_DIR` or `~/.claude`.

## 6. Known limits
- The weighted-token conversion (fresh input x1, cache write x1.25, cache read x0.1, output x5) is an estimate, not the provider's formula; the Fable share and the Fable % estimate can be off.
- A per-model limit key appears only if your Claude Code version sends one; the skill accepts any key containing "fable".
- Language: the default output uses the legacy Vietnamese labels and reminder text (`tong`, `XANH`/`VANG`/`DO`/`DU`); set `USAGE_TRACKER_LANG=en` for English (`of total`, GREEN/YELLOW/RED/SPARE). The Vietnamese messages live in `scripts/lang_vi.py`.
