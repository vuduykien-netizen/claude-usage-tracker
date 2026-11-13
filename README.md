# claude-usage-tracker

A Claude Code skill that shows your usage limits right on the status line, together with a weekly pace light and your Fable share. Pure Python 3 standard library, no dependencies, works on Windows, macOS and Linux. MIT licensed.

```text
Usage 5h 23% | Fable 17% of total | 7d usage 56% | 7d time 48% | YELLOW
```

That is the line you get with `USAGE_TRACKER_LANG=en`. Without the variable the same line uses the legacy Vietnamese labels (`tong`, `XANH`/`VANG`/`DO`/`DU`) and the per-prompt reminder is in Vietnamese; see [Language](#language).

## What the status line shows

| Field | Meaning |
|---|---|
| `5h` | Percent of the 5-hour limit used (the real number sent by Claude Code). |
| `Fable` | `17%`: a real per-model limit, if your Claude Code sends one. `~17%`: an estimate from a `/usage` marker you logged. `17% of total`: Fable's share of this week's usage, computed from your transcripts. |
| `7d usage` | Percent of the 7-day limit used (the real number). |
| `7d time` | Percent of the 7-day window that has already elapsed, computed from `seven_day.resets_at`. |
| light | Weekly pace: `GREEN` on pace, `YELLOW` a little ahead of schedule, `RED` far ahead of schedule, `SPARE` headroom left. |

On every prompt you type, a `UserPromptSubmit` hook adds a one-line reminder with the same numbers (plus a hint to lighten the load when the light is yellow or red, or the 5-hour window is at 75% or more). Numbers appear only after Claude Code has sent `rate_limits`, which requires a login plan that has limits and happens after your first message.

## How the pace light works

The light compares how much of the 7-day limit you have used with how much of the week has passed.

- `RED`: 7d usage is more than 10 points ahead of 7d time, or 7d usage is at 95% or more.
- `YELLOW`: more than 3 points ahead.
- `SPARE`: more than 8 points behind, so you have headroom.
- `GREEN`: anything in between.

Example: 56% used when 48% of the week has elapsed is 8 points ahead, which is `YELLOW`.

## Install (3 steps)

1. Put this folder at `~/.claude/skills/theo-doi-usage/` (or `$CLAUDE_CONFIG_DIR/skills/theo-doi-usage/`).
2. Preview: `python3 ~/.claude/skills/theo-doi-usage/install.py --dry-run`
3. Install: `python3 ~/.claude/skills/theo-doi-usage/install.py`, then restart Claude Code.

What `install.py` does: backs up `settings.json` (`settings.json.usage-tracker.<time>.bak`), copies the scripts to `<config>/usage-tracker/bin/`, adds a `statusLine` if you do not have one, adds one `UserPromptSubmit` hook group (your existing hooks are kept) and keeps every other key. If you already have a status line it is **not overwritten**: the installer prints the command to chain instead, for example forwarding the stdin JSON from your own script to `statusline_usage.py --quiet` (which only records the numbers and prints nothing).

On Windows use `py -3` or `python` instead of `python3` if needed. `<config>` is `CLAUDE_CONFIG_DIR`, `~/.claude` by default.

## Usage

- Install it once; after that the status line and the reminder update on their own.
- For a detailed weekly report, run `python3 ~/.claude/skills/theo-doi-usage/scripts/nhip_tuan.py` with no arguments.
- Ask Claude things like "how much of my week is left?" or "how much Fable have I used?" and it will run that report for you.

### Log a marker for a more accurate Fable % (optional)

Open `/usage`, read "week (all models)" and "week Fable", then run:

```text
python3 ~/.claude/skills/theo-doi-usage/scripts/nhip_tuan.py --moc 73 47
```

Add `--luc "2026-01-15 13:05"` if you read the numbers at another time. `--moc 73` logs the week number only.

## Language

The status line and the reminder have two label sets. For backward compatibility the default is still the Vietnamese one; set `USAGE_TRACKER_LANG=en` for English. The Vietnamese messages live in one file, `scripts/lang_vi.py`.

| | default | `USAGE_TRACKER_LANG=en` |
|---|---|---|
| Fable share label | `Fable 17% tong` | `Fable 17% of total` |
| Pace light | `XANH` / `VANG` / `DO` / `DU` | `GREEN` / `YELLOW` / `RED` / `SPARE` |
| Reminder and report text | Vietnamese | English |

## Uninstall safely

`python3 ~/.claude/skills/theo-doi-usage/install.py --uninstall` (add `--dry-run` to preview) only:

- removes the `statusLine` **if the skill set it**, removes exactly the hook the skill added (your other hooks and keys stay), and backs up `settings.json` first;
- deletes exactly the script files the skill copied into `<config>/usage-tracker/bin/`.

It never touches your config directory. The data in `<config>/usage-tracker/` (`rate.json`, `moc.jsonl`, `nhip-cache.json`) is kept; delete the `usage-tracker` folder by hand if you no longer need it. If you chained `statusline_usage.py --quiet` into your own script, remove that line by hand.

## FAQ

**Why does the status line show `-` for 5h or 7d?** Claude Code only sends the windows it knows about. A window that is not open yet (for example the 5-hour window before your first message) shows `-`; the last known value of the other window is kept.

**Why is there no Fable field?** The field appears only if Claude Code sends a per-model limit, you logged a `/usage` marker, or there is at least one Fable turn in this week's transcripts.

**How accurate is the Fable share?** It is an estimate. Usage is converted to weighted tokens (fresh input x1, cache write x1.25, cache read x0.1, output x5), which is not the provider's formula, so the share and the marker-based estimate can be off. A per-model limit key is only used if your Claude Code version sends one with "fable" in its name.

**Does it need a network connection or my login?** No. It makes no network calls and reads no credentials.

**Does it read my conversations?** No. See [Privacy](#privacy).

## Privacy

It reads only three fields, `model`, `usage` and `timestamp`, from your transcripts (`<config>/projects/**/*.jsonl`). It does not read conversation content, does not call the network and does not read login credentials.

## Tests

`python3 tests/kiem_thu.py` (uses a temporary directory and never touches your real config). `--pha` sets deliberately wrong expectations so you can confirm the suite catches them (prints `caught N/total`).

## Files

`SKILL.md` · `install.py` · `scripts/statusline_usage.py` · `scripts/hook_usage.py` · `scripts/nhip_tuan.py` · `scripts/usage_chung.py` · `scripts/lang_vi.py` · `tests/kiem_thu.py` · `LICENSE`

## License

MIT, see [LICENSE](LICENSE).
