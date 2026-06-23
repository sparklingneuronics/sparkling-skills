# VHS tape — records a full, uncut `dispatch` second-opinion session.
# Run from the prepared workspace copy (see README.md); outputs dispatch-session-full.mp4
# into the current directory. Then watch it, pick keep-ranges, and run render.py.

Output dispatch-session-full.mp4
Require claude
Set FontSize 18
Set Width 1280
Set Height 800
Set TypingSpeed 50ms

# launch off-camera (YOLO mode so nothing stalls on permissions — a normal power-user session)
Hide
Type "claude --dangerously-skip-permissions"
Enter
Sleep 8s
Enter
Sleep 3s
Show

# the ask: parallel red-team + a short verdict so it streams cleanly and fits on screen
Type "Before I run this backfill migration (migrations/0042_backfill_credits.py) in production, get a second opinion from codex and agy in parallel - red-team it for data-loss risks. Keep your answer to a few lines: the single most serious issue, and whether it's safe to run as-is."
Sleep 1s
Enter

# record the whole session uncut (thinking + codex/agy + the streaming verdict). render.py trims it.
Sleep 280s
