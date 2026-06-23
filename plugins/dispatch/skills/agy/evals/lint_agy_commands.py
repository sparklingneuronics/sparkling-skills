#!/usr/bin/env python3
"""
lint_agy_commands.py — drift check for the `agy` (Antigravity CLI) skill.

Sibling of the codex/gemini lints, adapted for `agy`, whose `--help` is
**Go-flag** formatted ("Usage of agy:" + one `--flag   description` per line +
an "Available subcommands:" section) — a third layout after codex's clap and
gemini's yargs. Extracts every `agy …` command from the skill's markdown
(SKILL.md + references/flags.md) and validates each command's subcommand path
and flags against the *installed* agy CLI's own `--help`.

Guards the skill's #1 failure mode: CLI drift. agy is brand-new (v1.0.x) and
moves fast — when it renames/moves/removes a flag, a documented command
silently breaks. This fails loudly instead — deterministically, offline (help
is local; no auth/network), no LLM.

Usage:
    python3 evals/lint_agy_commands.py              # lint the sibling skill
    python3 evals/lint_agy_commands.py --skill DIR
    python3 evals/lint_agy_commands.py --verbose

Exit codes:
    0  all documented commands are valid against the installed CLI
    1  at least one command uses an unknown subcommand or flag (drift)
    2  could not validate (agy not on PATH)

Cross-platform: pure Python 3 stdlib — runs on Windows, macOS, and Linux.
"""
from __future__ import annotations

import argparse
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

CLI = "agy"

# Known agy subcommand words, used to peel a subcommand chain out of a
# command's tokens.
SUBCOMMANDS = {
    "changelog", "help", "install", "models", "plugin", "plugins", "update",
}

# Flags that consume the following token as their value (so a value like a model
# string, conversation id, dir, or path is never mistaken for a subcommand).
VALUE_FLAGS = {
    "-p", "--print", "--prompt",
    "-i", "--prompt-interactive",
    "--model", "--conversation",
    "--add-dir", "--print-timeout", "--log-file",
}

# Flags every command accepts; never treat these as drift. (`--version` works
# even though it isn't printed in the top-level help.)
ALWAYS_OK = {"-h", "--help", "-v", "--version"}

SPLIT_OPERATORS = re.compile(r"\|\||&&|[|;]")  # pipe / and / semicolon / or

# Markers that identify real help output (agy: "Usage of agy:" + "Available
# subcommands:"). Used to tell a valid subcommand path from an error.
HELP_MARKERS = ("Usage", "subcommand")


def parse_help_flags(help_text: str) -> set[str]:
    """Extract flag tokens (-x / --xyz) from the option lines of a --help dump.
    Works across clap (codex), yargs (gemini), and Go-flag (agy) layouts: in all
    three, option lines start (after indent) with a dash-flag, and the flags sit
    before the first 2-space gap / `<` / `[`."""
    flags: set[str] = set()
    for line in help_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        if stripped.startswith("- "):  # a "possible values" bullet, not an option
            continue
        head = re.split(r"\s{2,}|<|\[", stripped, maxsplit=1)[0]
        for tok in re.findall(r"-{1,2}[A-Za-z][\w-]*", head):
            flags.add(tok)
    return flags


def get_help_flags(chain: tuple[str, ...], cache: dict) -> set[str] | None:
    """Valid flag set for `agy <chain>`, or None if that subcommand path is
    unknown to the installed CLI."""
    if chain in cache:
        return cache[chain]
    try:
        proc = subprocess.run(
            [CLI, *chain, "--help"],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        cache[chain] = None
        return None
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    # An invalid subcommand path makes the CLI error instead of printing help.
    if proc.returncode != 0 and not any(m in text for m in HELP_MARKERS):
        cache[chain] = None
        return None
    flags = parse_help_flags(text)
    cache[chain] = flags
    return flags


def split_command(command: str) -> tuple[tuple[str, ...], list[str]]:
    """Split an `agy …` command into (subcommand_chain, flags_used)."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    tokens = tokens[1:]  # drop leading "agy"
    chain: list[str] = []
    flags: list[str] = []
    expect_value = False
    for tok in tokens:
        if expect_value:
            expect_value = False
            continue
        if tok == "--":
            continue
        if tok.startswith("-") and tok != "-":
            flag = tok.split("=", 1)[0]
            flags.append(flag)
            if flag in VALUE_FLAGS and "=" not in tok:
                expect_value = True
        elif tok in SUBCOMMANDS:
            chain.append(tok)
        # else: positional / value / placeholder -> ignore
    return tuple(chain), flags


def extract_commands(md: str) -> list[tuple[int, str]]:
    """(line_number, command) for every agy invocation in a fenced code block.
    Skips blocks that are clearly captured --help output."""
    out: list[tuple[int, str]] = []
    in_block = False
    block: list[tuple[int, str]] = []
    for i, line in enumerate(md.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            if in_block:
                text = "\n".join(t for _, t in block)
                if not any(m in text for m in ("Usage of", "Available subcommands")):
                    out.extend(scan_block(block))
                block = []
            in_block = not in_block
            continue
        if in_block:
            block.append((i, line))
    return out


def scan_block(block: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Find agy invocations in a code block, joining `\\`-continued lines and
    splitting on shell operators so `… | agy …` and `… && agy …` count."""
    merged: list[tuple[int, str]] = []
    buf, buf_line = "", None
    for ln, text in block:
        if buf_line is None:
            buf_line = ln
        if text.rstrip().endswith("\\"):
            buf += text.rstrip()[:-1] + " "
        else:
            merged.append((buf_line, buf + text))
            buf, buf_line = "", None
    if buf:
        merged.append((buf_line or 0, buf))

    found: list[tuple[int, str]] = []
    for ln, text in merged:
        for seg in SPLIT_OPERATORS.split(text):
            seg = seg.strip()
            if re.match(rf"^{CLI}(\s|$)", seg):
                found.append((ln, seg))
    return found


def lint_file(path: Path, cache: dict, verbose: bool) -> list[str]:
    problems: list[str] = []
    for ln, command in extract_commands(path.read_text(encoding="utf-8")):
        chain, flags = split_command(command)
        valid = get_help_flags(chain, cache)
        loc = f"{path.name}:{ln}"
        if valid is None:
            problems.append(
                f"{loc}: unknown subcommand path `{CLI} {' '.join(chain)}`\n"
                f"        {command}"
            )
            continue
        unknown = [f for f in flags if f not in valid and f not in ALWAYS_OK]
        if unknown:
            problems.append(
                f"{loc}: `{CLI} {' '.join(chain) or '(top-level)'}` rejects "
                f"{', '.join(unknown)}\n        {command}"
            )
        elif verbose:
            shown = " ".join(chain) or "(top-level)"
            print(f"  ok  {loc}: {CLI} {shown}  flags=[{', '.join(flags)}]")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    ap.add_argument("--skill", type=Path, default=here.parent,
                    help="skill directory (default: the parent of this evals/ dir)")
    ap.add_argument("--verbose", action="store_true",
                    help="print every command checked, not just failures")
    args = ap.parse_args()

    if shutil.which(CLI) is None:
        print(f"{CLI} not on PATH — cannot validate. Install {CLI} (or run this "
              "where it is available) and retry.", file=sys.stderr)
        return 2

    version = subprocess.run([CLI, "--version"], capture_output=True,
                             text=True).stdout.strip() or "?"
    print(f"Linting `{args.skill.name}` skill commands against {CLI} {version}\n")

    targets = [args.skill / "SKILL.md", args.skill / "references" / "flags.md"]
    missing = [p for p in targets if not p.exists()]
    if missing:
        for p in missing:
            print(f"✗ required lint target missing: {p}", file=sys.stderr)
        return 1
    cache: dict = {}
    all_problems: list[str] = []
    checked = 0
    for path in targets:
        checked += len(extract_commands(path.read_text(encoding="utf-8")))
        all_problems.extend(lint_file(path, cache, args.verbose))

    if checked == 0:
        print(f"✗ zero {CLI} commands extracted — lint coverage is empty",
              file=sys.stderr)
        return 1

    print()
    if all_problems:
        print(f"✗ {len(all_problems)} issue(s) across {checked} command(s):\n")
        for p in all_problems:
            print(f"  ✗ {p}")
        print("\nRefresh `references/flags.md` against the new CLI, fix the "
              "commands above, and re-run.")
        return 1

    print(f"✓ all {checked} documented {CLI} commands are valid against {CLI} {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
