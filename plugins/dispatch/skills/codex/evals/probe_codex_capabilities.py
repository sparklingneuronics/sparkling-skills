#!/usr/bin/env python3
"""
probe_codex_capabilities.py — semantic drift check for the `codex` skill.

The sibling `lint_codex_commands.py` validates that every documented command
uses *flag names* the installed CLI accepts. That is necessary but not
sufficient: it cannot see whether two individually-valid flags may be combined,
which values a flag accepts, or which model/effort pairs the API will actually
serve. Those are exactly the facts that went stale between codex 0.144 and
0.153, and each one produced a documented command that parsed fine and failed
at runtime.

This probe covers that gap in two tiers:

  Tier 1 — invariants (FREE, ~2s)
      Assertions that resolve at argument-parse or config-load time, before any
      network call. Also *derives* the valid value sets for `--sandbox` and
      `web_search` from the CLI's own rejection messages, so a new or removed
      mode shows up as a diff rather than a surprise.

  Tier 2 — model x effort matrix (PAID, opt-in via --matrix)
      One real `codex exec` per cell. Emits the markdown table that lives in
      `references/flags.md`. This is what caught `gpt-6-astra` rejecting
      `none`, `gpt-5.4-mini` rejecting `max`, and `minimal` failing for two
      different reasons depending on the model.

Usage:
    python3 evals/probe_codex_capabilities.py                # tier 1 only (free)
    python3 evals/probe_codex_capabilities.py --matrix       # + tier 2 (paid)
    python3 evals/probe_codex_capabilities.py --matrix --markdown
                                                            # print the flags.md table
    python3 evals/probe_codex_capabilities.py --matrix --json OUT.json

Exit codes:
    0  every invariant held
    1  an invariant broke (the docs and the CLI disagree)
    2  could not validate (codex not on PATH)

Cross-platform: pure Python 3 stdlib — runs on Windows, macOS, and Linux.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import shutil
import subprocess
import sys

TRIVIAL_PROMPT = "Reply with exactly the single word OK and nothing else."

# Models to sweep in tier 2. Discovered from the CLI's embedded presets when
# possible (so a newly shipped model is picked up automatically); this list is
# the fallback and the ordering hint.
FALLBACK_MODELS = [
    "gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
    "gpt-5.5", "gpt-5.4-mini",
]
EFFORTS = ["none", "low", "medium", "high", "xhigh", "max", "ultra", "minimal"]

HDR = re.compile(r"^(model|reasoning effort):\s*(.+)$", re.M)
ERRMSG = re.compile(r'"message":\s*"([^"]+)"')


def run(args: list[str], timeout: int = 300) -> tuple[int, str, str]:
    try:
        p = subprocess.run(["codex", *args], capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"


# ---------------------------------------------------------------- tier 1


class Invariants:
    """Free checks. Each returns (ok, detail)."""

    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, ok: bool, detail: str) -> None:
        self.results.append((name, ok, detail))

    # -- helpers ---------------------------------------------------
    @staticmethod
    def _rejects(args: list[str], needle: str) -> tuple[bool, str]:
        """True when the CLI refuses `args` with a message containing needle."""
        rc, out, err = run(args, timeout=30)
        blob = (out + err).lower()
        return (rc != 0 and needle.lower() in blob), (out + err).strip().splitlines()[0][:120] if (out + err).strip() else f"rc={rc}"

    @staticmethod
    def _help_flags(chain: list[str]) -> set[str]:
        """Flags for `codex <chain>`, or an EMPTY set if the chain doesn't exist.

        An unknown subcommand exits 0 and prints the parent's help, so without
        the Usage: check below a nonexistent chain returns a full (superset)
        flag list and any "does this subcommand exist?" assertion built on it
        can never fail.
        """
        rc, out, err = run([*chain, "--help"], timeout=30)
        text = out + "\n" + err
        usage = next((ln for ln in text.splitlines()
                      if ln.strip().startswith("Usage:")), "")
        if rc != 0 or not usage.strip().startswith(
                "Usage: " + " ".join(("codex", *chain)) + " "):
            return set()
        flags: set[str] = set()
        for line in text.splitlines():
            s = line.strip()
            if not s.startswith("-") or s.startswith("- "):
                continue
            head = re.split(r"\s{2,}|<|\[", s, maxsplit=1)[0]
            flags.update(re.findall(r"-{1,2}[A-Za-z][\w-]*", head))
        return flags

    @staticmethod
    def _variants(args: list[str], key: str) -> list[str]:
        """Coax the CLI into enumerating a flag/config's legal values."""
        _, out, err = run(args, timeout=30)
        blob = out + err
        m = re.search(r"expected one of (.+)", blob)
        if m:
            return re.findall(r"[`']([\w-]+)[`']", m.group(1))
        m = re.search(r"\[possible values: ([^\]]+)\]", blob)
        if m:
            return [v.strip() for v in m.group(1).split(",")]
        return []

    # -- the invariants -------------------------------------------
    def run_all(self) -> None:
        # `codex exec` is non-interactive: approval flags belong to the TUI.
        ok, d = self._rejects(["exec", "-a", "never", "x"], "unexpected argument")
        self.check("codex exec rejects -a/--ask-for-approval", ok, d)

        ok, d = self._rejects(["exec", "--search", "x"], "unexpected argument")
        self.check("codex exec rejects --search (use -c web_search=)", ok, d)

        # The one that bit us: individually valid, mutually exclusive.
        ok, d = self._rejects(["exec", "--approve-for-me", "--sandbox", "read-only", "x"],
                              "cannot be used with")
        self.check("--approve-for-me conflicts with --sandbox", ok, d)

        # Top-level review operates on git state and refuses the escape hatch.
        ok, d = self._rejects(["review", "--skip-git-repo-check"], "unexpected argument")
        self.check("codex review rejects --skip-git-repo-check", ok, d)

        # The review split: only the exec form is scriptable.
        top = self._help_flags(["review"])
        ex = self._help_flags(["exec", "review"])
        ok = ("-m" not in top) and {"-m", "-o", "--json"} <= ex
        self.check("codex review lacks -m/-o/--json; codex exec review has them",
                   ok, f"review={sorted(top & {'-m','-o','--json'})} "
                       f"exec_review={sorted(ex & {'-m','-o','--json'})}")

        # fork: the top-level one is the interactive picker.
        fork_ex = self._help_flags(["exec", "fork"])
        self.check("codex exec fork exists (scriptable branch)",
                   bool(fork_ex), f"{len(fork_ex)} flags")

        # Value sets, derived from the CLI's own error text.
        sandboxes = self._variants(["exec", "-s", "__bogus__", "x"], "sandbox")
        self.check("sandbox values == read-only/workspace-write/danger-full-access",
                   sandboxes == ["read-only", "workspace-write", "danger-full-access"],
                   ", ".join(sandboxes) or "could not enumerate")

        websearch = self._variants(
            ["exec", "--strict-config", "-c", "web_search=__bogus__", "x"], "web_search")
        self.check("web_search modes == disabled/cached/indexed/live",
                   websearch == ["disabled", "cached", "indexed", "live"],
                   ", ".join(websearch) or "could not enumerate")


# ---------------------------------------------------------------- tier 2


def model_catalog() -> list[dict]:
    """The CLI's own resolved model catalog.

    `codex debug models` renders it as JSON — free, offline, and authoritative.
    Prefer it over anything derived from the binary: an earlier version of this
    function byte-scraped the `{"models": [...]}` blob embedded in the native
    executable, which turned out to be a *bundled* snapshot that disagrees with
    what the CLI actually resolves (it still listed `gpt-5.2`, which the catalog
    does not carry, and marked `gpt-5.4-mini` hidden when it is listed).
    """
    rc, out, _ = run(["debug", "models"], timeout=30)
    if rc != 0:
        return []
    try:
        return json.loads(out).get("models", [])
    except Exception:
        return []


def discover_models() -> list[str]:
    """Slugs to sweep in tier 2 — the user-selectable models."""
    slugs = [m["slug"] for m in model_catalog() if m.get("visibility") == "list"]
    return slugs or FALLBACK_MODELS


def probe_cell(model: str | None, effort: str | None) -> dict:
    args = ["exec", "--skip-git-repo-check", "--sandbox", "read-only"]
    if model:
        args += ["-m", model]
    if effort:
        args += ["-c", f"model_reasoning_effort={effort}"]
    args.append(TRIVIAL_PROMPT)
    rc, out, err = probe_cell_run(args)
    msg = ERRMSG.search(err)
    if msg:
        return {"model": model, "effort": effort, "ok": False, "detail": msg.group(1)}
    if rc != 0:
        first = err.strip().splitlines()[0][:140] if err.strip() else f"rc={rc}"
        return {"model": model, "effort": effort, "ok": False, "detail": first}
    return {"model": model, "effort": effort, "ok": bool(out.strip()),
            "detail": out.strip()[:40] or "empty output"}


def probe_cell_run(args: list[str]) -> tuple[int, str, str]:
    return run(args)


def run_matrix(models: list[str], workers: int) -> list[dict]:
    cells = [(m, e) for m in models for e in EFFORTS]
    print(f"  {len(cells)} paid calls ({len(models)} models x {len(EFFORTS)} efforts)…")
    out: list[dict] = []
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(probe_cell, m, e) for m, e in cells]
        for i, fut in enumerate(cf.as_completed(futs), 1):
            r = fut.result()
            out.append(r)
            mark = "ok " if r["ok"] else "ERR"
            print(f"    [{i:>2}/{len(cells)}] {mark} {str(r['model']):<16}"
                  f"{str(r['effort']):<9} {r['detail'][:70]}")
    return out


def markdown_table(results: list[dict], models: list[str]) -> str:
    grid = {(r["model"], r["effort"]): r["ok"] for r in results}
    head = "| Model | " + " | ".join(f"`{e}`" for e in EFFORTS) + " |"
    sep = "|---|" + ":--:|" * len(EFFORTS)
    rows = [
        "| `" + m + "` | " + " | ".join("✅" if grid.get((m, e)) else "❌" for e in EFFORTS) + " |"
        for m in models
    ]
    return "\n".join([head, sep, *rows])


# ---------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--matrix", action="store_true",
                    help="also run the PAID model x effort sweep")
    ap.add_argument("--markdown", action="store_true",
                    help="print the matrix as a markdown table for references/flags.md")
    ap.add_argument("--json", metavar="FILE", help="write raw matrix results to FILE")
    ap.add_argument("--workers", type=int, default=6, help="parallel calls (default 6)")
    args = ap.parse_args()

    if shutil.which("codex") is None:
        print("codex not on PATH — cannot probe.", file=sys.stderr)
        return 2

    version = run(["--version"], timeout=30)[1].strip()
    print(f"Probing codex capabilities against {version}\n")

    print("Tier 1 — invariants (free):")
    inv = Invariants()
    inv.run_all()
    for name, ok, detail in inv.results:
        print(f"  {'✓' if ok else '✗'} {name}")
        if not ok:
            print(f"      got: {detail}")
    failed = [n for n, ok, _ in inv.results if not ok]

    results: list[dict] = []
    if args.matrix:
        print("\nTier 2 — model x effort matrix (paid):")
        models = discover_models()
        results = run_matrix(models, args.workers)
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            print(f"\n  wrote {args.json}")
        if args.markdown:
            print("\n--- paste into references/flags.md ---")
            print(markdown_table(results, models))
            print("--- end ---")
        bad = [r for r in results if not r["ok"]]
        print(f"\n  {len(results) - len(bad)}/{len(results)} cells accepted")

    print()
    if failed:
        print(f"✗ {len(failed)} invariant(s) broke — the skill docs and the CLI "
              f"now disagree:\n    " + "\n    ".join(failed))
        print("\nUpdate `references/flags.md` / `SKILL.md` to match, then re-run.")
        return 1
    print(f"✓ all {len(inv.results)} invariants hold against {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
