---
description: Delegate a task to Google Antigravity's agy CLI (always invokes the agy skill)
argument-hint: "<task to delegate to agy>"
---
The user wants this **delegated to Google Antigravity (`agy`)** — run it through agy; do not answer it yourself. Invoke the `agy` skill and follow its workflow: pick a model (default Gemini 3.5 Flash; "with Claude Opus" / "Gemini Pro" to override), remember **agy acts by default** (no read-only mode — constrain via the prompt for analysis-only intent), allow a **generous timeout** (cold start can be ~2–3 min), and keep a topic-aware conversation so "continue with agy" resumes the right thread. If the request below is empty, delegate what the user is currently working on.

Request: $ARGUMENTS
