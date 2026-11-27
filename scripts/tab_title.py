#!/usr/bin/env python3
"""Name the terminal tab after the project Claude Code is working in.

Run as a SessionStart / UserPromptSubmit / Stop hook. Reads the hook JSON on
stdin (uses `cwd`, falls back to CLAUDE_PROJECT_DIR, then the current
directory) and prints {"terminalSequence": ESC ]0;<name> BEL}; Claude Code
writes that sequence to the terminal (interactive sessions only).

Name, first match wins:
  1. tab-names.json in <config>/usage-tracker/ : {"<folder>": "<tab name>"},
     longest folder that contains the working directory;
  2. the nearest parent folder (or the folder itself) holding .git or CLAUDE.md;
  3. the working directory's own folder name.
A leading "NN." numbering prefix ("05.My app" -> "My app") is dropped in 2 and 3.
Any error prints nothing and exits 0, so a session is never blocked.
"""
import json
import os
import re
import sys

MAX_LEN = 60


def config_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def norm(path):
    return os.path.normcase(os.path.normpath(path or "")).rstrip("\\/")


def strip_number(name):
    return re.sub(r"^\d+\.\s*", "", name) or name


def from_map(cwd):
    path = os.path.join(config_dir(), "usage-tracker", "tab-names.json")
    try:
        with open(path, encoding="utf-8") as f:
            table = json.load(f)
    except (OSError, ValueError):
        return None
    c, best, best_len = norm(cwd), None, -1
    for folder, name in table.items():
        f = norm(os.path.expanduser(folder))
        if (c == f or c.startswith(f + os.sep)) and len(f) > best_len and str(name).strip():
            best, best_len = str(name).strip(), len(f)
    return best


def from_root(cwd):
    d = os.path.normpath(cwd)
    while True:
        if os.path.exists(os.path.join(d, ".git")) or os.path.isfile(os.path.join(d, "CLAUDE.md")):
            return strip_number(os.path.basename(d)) if os.path.basename(d) else None
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def tab_name(cwd):
    name = from_map(cwd) or from_root(cwd) or strip_number(os.path.basename(os.path.normpath(cwd)) or "Claude")
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    return name if len(name) <= MAX_LEN else name[: MAX_LEN - 1] + "…"


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        data = {}
    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    sys.stdout.write(json.dumps({"terminalSequence": "\x1b]0;" + tab_name(cwd) + "\x07"}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
