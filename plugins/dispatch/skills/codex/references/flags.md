# `codex` CLI reference

Captured against `codex --version` = **codex-cli 0.141.0** (binary at `/opt/homebrew/bin/codex`). Re-run `codex exec --help`, `codex exec resume --help`, and `codex review --help` to refresh if the CLI is upgraded.

## Quick map (skill ↔ flag)

| Skill knob | Flag(s) | Notes |
|---|---|---|
| Prompt (one-shot) | positional `[PROMPT]` or stdin (use `-`) | When piped + positional, stdin is appended as `<stdin>` block |
| Model | `-m, --model <MODEL>` | Free-form string; codex doesn't enumerate |
| Reasoning effort | `-c model_reasoning_effort="<level>"` | `minimal\|low\|medium\|high\|xhigh` (default `medium`; the 0.141.0 CLI also accepts `none`). Passed via generic `-c key=value`. Works on `exec` and `exec resume` |
| Sandbox | `-s, --sandbox {read-only\|workspace-write\|danger-full-access}` | Default depends on user config |
| Approval (top-level only, NOT on `exec`) | `codex -a, --ask-for-approval {untrusted\|on-request\|never}` | Only applies to interactive `codex` runs. `codex exec` is inherently non-interactive and rejects `-a` |
| Working dir | `-C, --cd <DIR>` | Sets agent's working root |
| Extra writable dir | `--add-dir <DIR>` | Repeatable. Outside workspace |
| Skip git check | `--skip-git-repo-check` | Always include — avoids false-fail outside repos |
| Image attach | `-i, --image <FILE>` | Multi-modal. Repeatable on `exec`; single on `resume` |
| Profile | `-p, --profile <CONFIG_PROFILE_V2>` | Layers `$CODEX_HOME/<name>.config.toml` on top of base user config |
| Bypass everything (DANGER) | `--dangerously-bypass-approvals-and-sandbox` | Never set without explicit user OK on this call |
| Ephemeral | `--ephemeral` | Don't persist session to disk |
| Ignore user config | `--ignore-user-config` | Skips `~/.codex/config.toml` |
| Ignore project rules | `--ignore-rules` | Skips execpolicy `.rules` files |
| OSS provider | `--oss --local-provider {lmstudio\|ollama}` | Local model dispatch |
| Web search | `-c web_search="live"` (top-level config key) | The mode control. `--search` is a **TUI-only** flag that maps to this. `--enable web_search` still works but is **deprecated** (it warns → use the config key). Modes: `cached` (**default**; search is **on** by default, maintained index) · `live` (open web) · `disabled` |
| Feature toggle | `--enable <FEATURE>` / `--disable <FEATURE>` | Repeatable. Equivalent to `-c features.<name>=true\|false`. On `exec` and `exec resume` |
| JSON event stream | `--json` | JSONL events to stdout |
| Last message to file | `-o, --output-last-message <FILE>` | Only the final message goes to file |
| Strict output schema | `--output-schema <FILE>` | JSON Schema for the final response |
| Strict config | `--strict-config` | Error out on unrecognized `config.toml` fields |
| Bypass hook trust (DANGER) | `--dangerously-bypass-hook-trust` | Runs enabled hooks without persisted trust. Never set without explicit user OK |
| Color | `--color {auto\|always\|never}` | Default auto |

## Models

`-m` accepts any string — the CLI doesn't enumerate or validate model names in `--help`, so this is a curated guide, not an allow-list; names not listed may still work if your account/profile permits. Status for ChatGPT sign-in (as of codex-cli 0.141.0):

- `gpt-5.5` — **current default**, strongest all-round (deepest reasoning; the usual pick)
- `gpt-5.4` — flagship; the fallback if `gpt-5.5` isn't provisioned
- `gpt-5.4-mini` — fast and cheaper; good for light tasks and subagents
- `gpt-5.3-codex-spark` — ultra-fast text-only **research preview** (ChatGPT **Pro** only)
- `gpt-5.3-codex` — **deprecated** for ChatGPT sign-in (still works on API-key auth)

## Subcommands you may invoke

| Command | Purpose |
|---|---|
| `codex exec [PROMPT]` (alias `e`) | Non-interactive run — primary skill entry point |
| `codex exec resume [SESSION_ID] [PROMPT]` | Resume a previous session by UUID (a TUI-set thread name also works, but `exec`-created threads have only a UUID) |
| `codex exec resume --last [PROMPT]` | Resume most recent session |
| `codex review [PROMPT]` | Non-interactive code review against the current repo (top-level) |
| `codex exec review` | Same review, dispatched as a subcommand of `exec` |
| `codex fork` | Fork a previous session into a new branch (vs continuing it) |
| `codex resume` (top-level, interactive) | Picker-driven resume — drops into TUI |
| `codex doctor` | Diagnose local install, config, auth, and runtime health (useful for pre-flight / debugging auth) |
| `codex archive` / `unarchive` / `delete` | Manage saved sessions by id or thread name |
| `codex login` / `codex logout` | OAuth credential management |
| `codex mcp` | Manage external MCP servers for codex |
| `codex sandbox` | Run arbitrary commands inside codex's sandbox (debug aid) |
| `codex apply` | Apply codex's last diff as `git apply` |
| `codex features` | Inspect feature flags (names usable with `--enable`/`--disable`) |
| `codex update` | Self-update |

## Session ids & resume (the `--json` schema)

To keep multiple Codex threads alive and resume the *exact* one later, capture each thread's id at creation — the id is surfaced only on the `--json` event stream.

**`codex exec --json` stdout** is JSONL using the `ThreadEvent` schema:

| Event `type` | Carries | Path |
|---|---|---|
| `thread.started` (first line) | the session/thread id | `.thread_id` |
| `item.completed` with `item.type == "agent_message"` (last one) | the final answer text | `.item.text` |
| `turn.started` / `turn.completed` / `item.started` / `item.updated` / `error` | progress / usage / errors | — |

Read `.thread_id` from the **first line** to capture the id; read the final answer from the last `agent_message`, or just use `-o <FILE>` (writes only the final message). Ids are **UUIDv7** — 36-char hyphenated, e.g. `0199a213-81c0-7800-8aa1-bbab2a035a53`.

```bash
# start a thread: capture id, keep the event stream out of context, answer to a file
codex exec --json --skip-git-repo-check --sandbox read-only -o /tmp/ans.txt "<prompt>" 2>/dev/null > /tmp/events.jsonl
head -n 1 /tmp/events.jsonl      # → {"type":"thread.started","thread_id":"<UUID>"}  ← store this
#   /tmp/ans.txt → the final answer

# resume that exact thread later (id known, so no --json needed)
codex exec --skip-git-repo-check resume <UUID> -o /tmp/ans.txt "<follow-up>" 2>/dev/null
```

Gotchas:
- **Resume by UUID is not cwd-filtered** (works from any directory). Resume by *thread name* or `--last` IS cwd-filtered unless you add `--all`.
- **You can't set the id (or a thread name) at `exec` creation** — there's no flag; the id is auto-generated, so capture it from `thread.started`. (Thread names can only be set in the interactive TUI.)
- **Don't pipe the live `--json` run into `head -1`/`grep -m1`** — the pipe close SIGPIPEs Codex mid-turn and aborts it before the answer / `-o` file is written. Read the first line from the full captured output, or redirect to a file and read it *after* Codex exits.
- The persisted **rollout file** (`~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<id>.jsonl`) uses a *different* shape — `{"type":"session_meta","payload":{"id":...}}`. Don't confuse it with the `--json` stdout stream.

## Common patterns

**One-shot, read-only review:**
```bash
codex exec -m gpt-5.5 -c model_reasoning_effort="high" --sandbox read-only --skip-git-repo-check "review this function for race conditions" 2>/dev/null
```

**Refactor with edits in workspace:**
```bash
codex exec -m gpt-5.5 -c model_reasoning_effort="high" --sandbox workspace-write --skip-git-repo-check "rename foo to bar across the repo" 2>/dev/null
```

**Full autonomy (only with explicit user OK):**
```bash
codex exec -m gpt-5.5 -c model_reasoning_effort="xhigh" --sandbox danger-full-access --skip-git-repo-check "implement the spec in PLAN.md and run the tests" 2>/dev/null
```

**Long prompt via stdin:**
```bash
cat <<'EOF' | codex exec -m gpt-5.5 -c model_reasoning_effort="medium" --sandbox read-only --skip-git-repo-check - 2>/dev/null
<paste long prompt here>
EOF
```

**Resume the last session (sandbox inherited; `-m`/effort can be overridden):**
```bash
echo "now also add tests" | codex exec --skip-git-repo-check resume --last 2>/dev/null
```
> `exec resume` accepts `-m, --model` and `-c model_reasoning_effort=...` (override if you must), but has **no `-s, --sandbox`** — the sandbox is inherited from the original session. Add `--all` to disable cwd-filtering so `--last` resolves to the newest session across all working dirs. (For topic routing the skill resumes by **stored UUID**, not `--last` — see *Session ids & resume* above.)

**Resume a specific session by id or thread name:**
```bash
echo "follow-up question" | codex exec --skip-git-repo-check resume <UUID-or-thread-name> 2>/dev/null
```

**Structured output for parsing:**
```bash
codex exec -m gpt-5.4-mini --sandbox read-only --skip-git-repo-check --json "list TODOs in src/, return JSON array of {file,line,text}" 2>/dev/null
```

**Save only the final message to a file:**
```bash
codex exec -m gpt-5.5 --sandbox read-only --skip-git-repo-check -o /tmp/last.md "summarize CONTRIBUTING.md" 2>/dev/null
```

**Code review (current changes vs. default):**
```bash
codex review 2>/dev/null
```
> `codex review` does **not** accept `--skip-git-repo-check` (it operates on git changes, so a repo is required). Target the review with: `--uncommitted` (staged + unstaged + untracked), `--base <branch>` (diff against a branch), `--commit <sha>` (one commit), and `--title <title>` for the summary header. Custom instructions go as the `[PROMPT]` positional (or via `-` on stdin).

```bash
codex review --uncommitted 2>/dev/null
codex review --base main 2>/dev/null
```

## Verbatim `codex --help` (top-level)

```
Codex CLI

If no subcommand is specified, options will be forwarded to the interactive CLI.

Usage: codex [OPTIONS] [PROMPT]
       codex [OPTIONS] <COMMAND> [ARGS]

Commands:
  exec            Run Codex non-interactively [aliases: e]
  review          Run a code review non-interactively
  login           Manage login
  logout          Remove stored authentication credentials
  mcp             Manage external MCP servers for Codex
  plugin          Manage Codex plugins
  mcp-server      Start Codex as an MCP server (stdio)
  app-server      [experimental] Run the app server or related tooling
  remote-control  [experimental] Manage the app-server daemon with remote control enabled
  app             Launch the Codex desktop app (opens the app installer if missing)
  completion      Generate shell completion scripts
  update          Update Codex to the latest version
  doctor          Diagnose local Codex installation, config, auth, and runtime health
  sandbox         Run commands within a Codex-provided sandbox
  debug           Debugging tools
  apply           Apply the latest diff produced by Codex agent as a `git apply` to your local
                  working tree [aliases: a]
  resume          Resume a previous interactive session (picker by default; use --last to continue
                  the most recent)
  archive         Archive a saved session by id or session name
  delete          Permanently delete a saved session by id or session name
  unarchive       Unarchive a saved session by id or session name
  fork            Fork a previous interactive session (picker by default; use --last to fork the
                  most recent)
  cloud           [EXPERIMENTAL] Browse tasks from Codex Cloud and apply changes locally
  exec-server     [EXPERIMENTAL] Run the standalone exec-server service
  features        Inspect feature flags
  help            Print this message or the help of the given subcommand(s)
```

(Full help body — including all options on `exec` and `exec resume` — is captured in this skill's design notes; re-run `codex exec --help` and `codex exec resume --help` if you need it verbatim again.)
