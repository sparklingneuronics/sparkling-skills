#!/usr/bin/env python3
"""
fake_codex.py — a stand-in `codex` that records how it was called.

Used by `probe_skill_behavior.py`. It never talks to OpenAI: it appends one
JSON line per invocation to $FAKE_CODEX_LOG, then emits just enough
well-formed output that the skill's documented flow keeps working — a
`thread.started` event on `--json`, an answer written to `-o`, a run header on
stderr, exit 0.

That fidelity is the point. The skill captures a thread id from the `--json`
stream and resumes it later; if the fake didn't hand back a usable id, we
couldn't test whether the skill resumes the *right* one.

Thread ids are deterministic (`00000000-0000-4000-8000-0000000000NN`, NN =
invocation number) so assertions can name them.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

LOG = Path(os.environ.get("FAKE_CODEX_LOG", "fake_codex.log.jsonl"))
ANSWER = os.environ.get("FAKE_CODEX_ANSWER", "Looks fine to me. One nit: the "
                                              "loop re-reads the file each pass.")


def thread_id(n: int) -> str:
    return f"00000000-0000-4000-8000-{n:012d}"


def main(argv: list[str]) -> int:
    # Read stdin only when the prompt is explicitly `-`, which is how the skill
    # documents the piped path. Reading unconditionally deadlocks: an inherited
    # pipe that nobody writes to is neither a tty nor EOF, so read() blocks.
    stdin_data = ""
    if "-" in argv:
        try:
            stdin_data = sys.stdin.read()
        except Exception:
            stdin_data = ""

    LOG.parent.mkdir(parents=True, exist_ok=True)
    # Number threads by *delegating* calls only. `--help` probes are logged (the
    # analyzer wants to see them) but must not consume an id: the analyzer
    # filters them out, so counting them would shift every id and make an
    # assertion like "resumed thread ...0001" fail whenever Claude happened to
    # check syntax first.
    is_help = "--help" in argv or "-h" in argv
    prior = 0
    if LOG.exists():
        for line in LOG.open(encoding="utf-8"):
            if line.strip():
                try:
                    if not json.loads(line).get("help"):
                        prior += 1
                except ValueError:
                    pass
    n = prior if is_help else prior + 1
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "n": n, "help": is_help, "argv": argv,
            "cwd": os.getcwd(), "stdin": stdin_data,
        }) + "\n")

    tid = thread_id(max(n, 1))

    # Mimic the real run header (stderr) — the skill suppresses it with
    # 2>/dev/null, so anything we print here must not be load-bearing.
    print(f"OpenAI Codex v0.153.4 (fake)\n--------\nworkdir: {os.getcwd()}\n"
          f"model: gpt-6-astra\nsandbox: read-only\nsession id: {tid}\n--------",
          file=sys.stderr)

    # -o <FILE> captures only the final message.
    if "-o" in argv or "--output-last-message" in argv:
        key = "-o" if "-o" in argv else "--output-last-message"
        i = argv.index(key)
        if i + 1 < len(argv):
            try:
                Path(argv[i + 1]).write_text(ANSWER, encoding="utf-8")
            except OSError:
                pass

    if "--json" in argv:
        out = [
            {"type": "thread.started", "thread_id": tid},
            {"type": "turn.started"},
            {"type": "item.completed",
             "item": {"id": "item_0", "type": "agent_message", "text": ANSWER}},
            {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}},
        ]
        for ev in out:
            print(json.dumps(ev))
    else:
        print(ANSWER)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
