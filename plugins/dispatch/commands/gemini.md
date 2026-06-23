---
description: Delegate a task to a Gemini model via Antigravity's agy CLI (invokes the agy skill)
argument-hint: "<task to delegate to gemini>"
---
The user wants this **delegated to Gemini** — run it through Antigravity's `agy` CLI with a Gemini model (gemini-cli's individual tier is retired; `agy` is the working successor). Do not answer it yourself. Invoke the `agy` skill and follow its workflow, using `--model "Gemini 3.1 Pro (High)"` (or `"Gemini 3.5 Flash (High)"` for a quick check). Remember **agy acts by default** (constrain via the prompt for analysis-only intent), allow a **generous timeout** (cold start can be ~2–3 min), and keep a topic-aware conversation so "continue with gemini" resumes the right thread. If the request below is empty, delegate what the user is currently working on.

Request: $ARGUMENTS
