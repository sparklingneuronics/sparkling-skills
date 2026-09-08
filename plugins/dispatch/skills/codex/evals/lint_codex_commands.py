#!/usr/bin/env python3
"""
lint_codex_commands.py — drift check for the `codex` skill.

Extracts every `codex ...` command embedded in the skill's markdown
(SKILL.md + references/flags.md) and validates each command's subcommand path
and flags against the *installed* codex CLI's own `--help` output.

This guards the skill's #1 failure mode: CLI drift. When codex renames, moves,
or removes a flag (e.g. `codex review --skip-git-repo-check` going from valid
to rejected), a documented command silently breaks. This lint fails loudly
instead — deterministically, offline (help is local; no OAuth, no network),
and with no LLM in the loop.

Usage:
    python evals/lint_codex_commands.py              # lint the sibling skill
    python evals/lint_codex_commands.py --skill DIR  # lint a specific skill dir
    python evals/lint_codex_commands.py --verbose     # show every command checked

Exit codes:
    0  all documented commands are valid against the installed CLI
    1  at least one command uses an unknown subcommand or flag (drift)
    2  could not validate (codex not on PATH)

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

# Known codex subcommand words, used to peel the subcommand chain out of a
# command's tokens (flags may be interleaved, e.g. `exec --foo resume`).
SUBCOMMANDS = {
    "exec", "resume", "review", "fork", "login", "logout", "mcp", "mcp-server",
    "app-server", "remote-control", "app", "completion", "update", "doctor",
    "sandbox", "debug", "apply", "archive", "delete", "unarchive", "cloud",
    "exec-server", "features", "plugin", "help",
    # added in codex-cli 0.153.x
    "agents", "queue", "migrate-rollouts",
}

# Flags that consume the following token as their value. We skip that token so
# a value like `read-only` or `gpt-5.5` is never mistaken for a subcommand.
VALUE_FLAGS = {
    "-m", "--model", "-c", "--config", "-C", "--cd", "-i", "--image",
    "-o", "--output-last-message", "--output-schema", "--add-dir",
    "-p", "--profile", "--base", "--commit", "--title", "--color",
    "--local-provider", "--enable", "--disable", "--remote",
    "--remote-auth-token-env", "-a", "--ask-for-approval", "-s", "--sandbox",
    # added in codex-cli 0.153.x
    "--thread", "--message", "--thread-source", "--max-mib-per-second",
}

# Flags every subcommand accepts; never treat these as drift.
ALWAYS_OK = {"-h", "--help", "-V", "--version"}

SPLIT_OPERATORS = re.compile(r"\|\||&&|[|;]")  # pipe / and / semicolon / or


def parse_help_flags(help_text: str) -> set[str]:
    """Extract flag tokens (-x / --xyz) from the option lines of a --help dump."""
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
    """Valid flag set for `codex <chain>`, or None if that subcommand path is
    unknown to the installed CLI."""
    if chain in cache:
        return cache[chain]
    try:
        proc = subprocess.run(
            ["codex", *chain, "--help"],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        cache[chain] = None
        return None
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    # An unknown subcommand does NOT error: codex exits 0 and prints the
    # *parent's* help, whose flag set is a strict superset. Checking the return
    # code alone would silently validate `codex exec bogus` against
    # `codex exec`, which is the drift this lint exists to catch. So require the
    # Usage: line to name the full chain.
    usage = next((ln for ln in text.splitlines()
                  if ln.strip().startswith("Usage:")), "")
    if proc.returncode != 0 or not usage:
        cache[chain] = None
        return None
    if not usage.strip().startswith("Usage: " + " ".join(("codex", *chain)) + " "):
        cache[chain] = None
        return None
    flags = parse_help_flags(text)
    cache[chain] = flags
    return flags


def split_command(command: str) -> tuple[tuple[str, ...], list[str]]:
    """Split a `codex ...` command into (subcommand_chain, flags_used)."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    tokens = tokens[1:]  # drop leading "codex"
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
    """(line_number, command) for every codex invocation in a fenced code
    block. Skips blocks that are clearly captured --help output."""
    out: list[tuple[int, str]] = []
    in_block = False
    block: list[tuple[int, str]] = []
    for i, line in enumerate(md.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            if in_block:
                text = "\n".join(t for _, t in block)
                if "Usage:" not in text and "Print this message" not in text:
                    out.extend(scan_block(block))
                block = []
            in_block = not in_block
            continue
        if in_block:
            block.append((i, line))
    return out


def scan_block(block: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Find codex invocations in a code block, joining `\\`-continued lines and
    splitting on shell operators so `… | codex …` and `… && codex …` count."""
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
            if re.match(r"^codex(\s|$)", seg):
                found.append((ln, seg))
    return found


def lint_file(path: Path, cache: dict, verbose: bool) -> list[str]:
    """Return a list of problem strings for one markdown file."""
    problems: list[str] = []
    commands = extract_commands(path.read_text(encoding="utf-8"))
    for ln, command in commands:
        chain, flags = split_command(command)
        valid = get_help_flags(chain, cache)
        loc = f"{path.name}:{ln}"
        if valid is None:
            problems.append(
                f"{loc}: unknown subcommand path `codex {' '.join(chain)}`\n"
                f"        {command}"
            )
            continue
        unknown = [f for f in flags if f not in valid and f not in ALWAYS_OK]
        if unknown:
            problems.append(
                f"{loc}: `codex {' '.join(chain) or '(top-level)'}` rejects "
                f"{', '.join(unknown)}\n        {command}"
            )
        elif verbose:
            shown = " ".join(chain) or "(top-level)"
            print(f"  ok  {loc}: codex {shown}  flags=[{', '.join(flags)}]")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    ap.add_argument("--skill", type=Path, default=here.parent,
                    help="skill directory (default: the parent of this evals/ dir)")
    ap.add_argument("--verbose", action="store_true",
                    help="print every command checked, not just failures")
    args = ap.parse_args()

    if shutil.which("codex") is None:
        print("codex not on PATH — cannot validate. Install codex (or run this "
              "where codex is available) and retry.", file=sys.stderr)
        return 2

    version = subprocess.run(["codex", "--version"], capture_output=True,
                             text=True).stdout.strip()
    print(f"Linting `{args.skill.name}` skill commands against {version}\n")

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
        cmds = extract_commands(path.read_text(encoding="utf-8"))
        checked += len(cmds)
        all_problems.extend(lint_file(path, cache, args.verbose))

    if checked == 0:
        print("✗ zero codex commands extracted — lint coverage is empty",
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

    print(f"✓ all {checked} documented codex commands are valid against {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
