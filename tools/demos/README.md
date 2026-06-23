# Demo tooling — record & regenerate the `dispatch` demo

The README hero GIF (`assets/dispatch-demo.gif`) and the LinkedIn MP4 (`assets/dispatch-demo.mp4`)
are generated from a **real** `dispatch` session — Claude getting a second opinion from `codex` and
`agy` on a planted data-loss bug. This folder makes regenerating them reproducible.

## What's here
| File | Purpose |
|---|---|
| `workspace/` | a throwaway repo with one **planted data-loss bug** (`migrations/0042_backfill_credits.py`) that codex + agy reliably catch |
| `dispatch-second-opinion.tape` | the VHS tape that records the full Claude Code session |
| `render.py` | turns a recorded session into the committed GIF + MP4 (cut → speed → final-frame hold → optimize) |

## Prerequisites
- `brew install vhs ffmpeg gifsicle`
- `codex login` + `agy` signed in, and the `dispatch` plugin available to Claude:
  `claude plugin install dispatch@sparkling-skills --scope user`

## Regenerate (3 steps)

**1. Record** the session (real, live — ~5 min):
```bash
cp -R tools/demos/workspace /tmp/dispatch-demo
( cd /tmp/dispatch-demo && git init -q && git add db.py README.md \
  && git -c commit.gpgsign=false -c user.email=demo@example.com -c user.name=demo commit -qm baseline )
# leaves migrations/0042_backfill_credits.py as the untracked change to review
( cd /tmp/dispatch-demo && vhs "$OLDPWD/tools/demos/dispatch-second-opinion.tape" )
# -> /tmp/dispatch-demo/dispatch-session-full.mp4
```

**2. Watch it and pick keep-ranges** — drop the dead model-wait and the verbose skill-reading;
keep the prompt, the parallel `codex`/`agy` run, and the streaming verdict.

**3. Render** (the example below reproduces the shipped demo):
```bash
python3 tools/demos/render.py /tmp/dispatch-demo/dispatch-session-full.mp4 \
  --keep 0:00-0:51 1:07-1:10 1:15-1:35 1:56-2:17 --speed 1.5
# -> assets/dispatch-demo.gif (900px, crisp, 2.5s final-frame hold) + assets/dispatch-demo.mp4
```

## Notes
- It's a **live AI session → non-deterministic**: expect 1–2 takes for a clean run, and re-pick
  keep-ranges each time (the timing shifts). This is the honest cost of recording the real tools.
- The GIF settings (900px = GitHub's column width, `dither=none`, `gifsicle --lossy=30`) are tuned
  for crisp terminal text under 5 MB — the rationale is in [`private/DEMO-RECORDING.md`](../../private/DEMO-RECORDING.md).
- Embed in the README as `<img src="assets/dispatch-demo.gif" width="900">` so GitHub renders it 1:1.
