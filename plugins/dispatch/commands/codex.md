---
description: Delegate a task to OpenAI Codex (always invokes the codex skill)
argument-hint: "<task to delegate to codex>"
---
The user wants this **delegated to OpenAI Codex** — run it through Codex; do not answer it yourself. Invoke the `codex` skill and follow its workflow: default to read-only and to codex's own default model (don't pin `-m`), confirm before any writable sandbox, and keep a topic-aware session so "continue with codex" resumes the right thread. If the request below is empty, delegate what the user is currently working on.

Request: $ARGUMENTS
