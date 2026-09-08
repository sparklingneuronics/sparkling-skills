# `codex` CLI reference

Captured against `codex --version` = **codex-cli 0.153.4** (binary at `/opt/homebrew/bin/codex`). Re-run `codex exec --help`, `codex exec resume --help`, `codex review --help`, and `codex exec review --help` to refresh if the CLI is upgraded.

## Quick map (skill ↔ flag)

| Skill knob | Flag(s) | Notes |
|---|---|---|
| Prompt (one-shot) | positional `[PROMPT]` or stdin (use `-`) | When piped + positional, stdin is appended as `<stdin>` block |
| Model | `-m, --model <MODEL>` | Free-form string; codex doesn't enumerate. **Omit it** to get the account/CLI default — see [Models](#models) |
| Reasoning effort | `-c model_reasoning_effort="<level>"` | `low\|medium\|high\|xhigh` are safe everywhere; `none`, `max`, `ultra` vary **per model** and `minimal` always fails — see the probe table in [Reasoning effort](#reasoning-effort) before pinning one. Passed via generic `-c key=value`. Works on `exec` and `exec resume` |
| Sandbox | `-s, --sandbox {read-only\|workspace-write\|danger-full-access}` | Default depends on user config. `workspace-write`'s writable roots default to **`[workdir, /tmp, $TMPDIR]`** — wider than the name implies. See [Sandbox behaviour](#sandbox-behaviour-verified) |
| Auto-reviewed approvals | `--approve-for-me` | Runs under `workspace-write` **and auto-grants escalations** — verified writing outside the workspace where plain `-s workspace-write` refused. **Mutually exclusive with `-s/--sandbox`**: combining them is a parse error (exit 2, no API call). Sits *above* `workspace-write` on the risk ladder, not below it. On `exec`, top-level, and `queue` |
| Approval (top-level only, NOT on `exec`) | `codex -a, --ask-for-approval {on-request\|never}` | Only applies to interactive `codex` runs. `codex exec` is inherently non-interactive and rejects `-a`. **`untrusted` was removed** in 0.153.x |
| Working dir | `-C, --cd <DIR>` | Sets agent's working root |
| Extra writable dir | `--add-dir <DIR>` | Repeatable. Outside workspace |
| Skip git check | `--skip-git-repo-check` | Always include on `exec` / `exec resume` / `exec review` — avoids false-fail outside repos. **Not** accepted by top-level `codex review` |
| Image attach | `-i, --image <FILE>` | Multi-modal. Repeatable on `exec`; single on `resume` |
| Profile | `-p, --profile <CONFIG_PROFILE_V2>` | Layers `$CODEX_HOME/<name>.config.toml` on top of base user config |
| Bypass everything (DANGER) | `--dangerously-bypass-approvals-and-sandbox` | Never set without explicit user OK on this call |
| Ephemeral | `--ephemeral` | Don't persist session to disk. Now also on `exec resume` / `exec review` |
| Ignore user config | `--ignore-user-config` | Skips `~/.codex/config.toml` |
| Ignore project rules | `--ignore-rules` | Skips execpolicy `.rules` files |
| Thread classification | `--thread-source <SOURCE>` | Source tag for newly created/forked threads. On `exec`, `exec resume`, `exec review` |
| OSS provider | `--oss --local-provider {lmstudio\|ollama}` | Local model dispatch |
| Web search | `-c web_search="live"` (top-level config key) | The mode control. Modes: `disabled` · `cached` · `indexed` · `live`. Search is **on by default**. `--search` is a **top-level flag** (not on `exec`). `--enable web_search` still works but is **deprecated** — it warns "web search is enabled by default" |
| Feature toggle | `--enable <FEATURE>` / `--disable <FEATURE>` | Repeatable. Equivalent to `-c features.<name>=true\|false`. Inspect names with `codex features list` |
| Remote app server | `--remote <ADDR>` / `--remote-auth-token-env <ENV_VAR>` | Drive a remote app-server (`ws://`, `wss://`, `unix://`). Top-level, `agents`, `queue` |
| JSON event stream | `--json` | JSONL events to stdout |
| Last message to file | `-o, --output-last-message <FILE>` | Only the final message goes to file |
| Strict output schema | `--output-schema <FILE>` | JSON Schema for the final response. Now also on `exec resume` / `exec review` |
| Strict config | `--strict-config` | Error out on unrecognized `config.toml` fields — useful for validating a `-c` key |
| Bypass hook trust (DANGER) | `--dangerously-bypass-hook-trust` | Runs enabled hooks without persisted trust. Never set without explicit user OK |
| Color | `--color {auto\|always\|never}` | Default auto. `exec` only (not `exec resume`) |

## Models

`-m` accepts any string — the CLI doesn't enumerate or validate model names in `--help`. **The skill's default is to omit `-m` entirely** and let codex use the account/CLI default. That's deliberate: model lineups churn every few releases, and a hardcoded id is the exact thing that goes stale between skill updates. Pass `-m` only when the user names a model, or when you have a specific reason (a cheap model for a trivial side task).

Availability below was probe-tested against the live API on **ChatGPT sign-in** (codex-cli 0.153.4). The lineup and per-model metadata come from the CLI's own embedded model presets. An API-key account may see a different set.

| Model | Status on ChatGPT sign-in | What it's for |
|---|---|---|
| `gpt-6-astra` | ✅ **the current default** | "Our most capable model for complex, demanding work." Needs codex ≥ **0.153.0** — don't hardcode it if you care about older CLIs |
| `gpt-5.6-sol` | ✅ available | "Latest frontier agentic coding model." Deepest 5.6 reasoning |
| `gpt-5.6-terra` | ✅ available | Balanced everyday workhorse — the old default |
| `gpt-5.6-luna` | ✅ available | Fastest and cheapest in the 5.6 family; good for light tasks |
| `gpt-5.5` | ✅ available | Previous generation. Effort caps at `xhigh` — `max` errors |
| `gpt-5.4-mini` | ⚠️ still accepted, but **retired** | Retirement date 2026-08-31, migrates to `gpt-5.6-luna`. Treat as going away; don't use in examples |
| `gpt-5.4` | ❌ rejected | Retired 2026-08-31 → `gpt-5.6-terra` |
| `gpt-5.6` (bare alias) | ❌ rejected | *"not supported when using Codex with a ChatGPT account"* |
| `gpt-5.6-pro` | ❌ rejected | Same — not on the ChatGPT path |
| `gpt-5.2` | ❌ rejected | Listed in presets but refused on ChatGPT sign-in |
| `gpt-5.2-codex`, `gpt-5.3-codex`, `gpt-5.3-codex-spark` | ❌ gone | Dropped from the presets entirely |
| `gpt-daybreak-blue-latest` / `gpt-daybreak-red-latest` | ❌ rejected | Cyber-specialty models (`model_specialty: cyber`) — blue is defensive, red is cyber-permissive for authorized work. Hidden; not on the ChatGPT path |
| `codex-auto-review` | internal | The model behind `--approve-for-me`. Not for direct use |

Context window is 272k on every current model (272k–872k max depending on model).

## Reasoning effort

Levels are **per-model** — there is no single valid set. This table is a full live probe of every model × effort combination on ChatGPT sign-in (codex-cli 0.153.4); ✅ = the call succeeded, ❌ = the API rejected it.

| Model | `none` | `low` | `medium` | `high` | `xhigh` | `max` | `ultra` | `minimal` |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `gpt-6-astra` | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `gpt-5.6-sol` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `gpt-5.6-terra` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `gpt-5.6-luna` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `gpt-5.5` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| `gpt-5.4-mini` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |

Regenerate with `python3 evals/probe_codex_capabilities.py --matrix --markdown`; it sweeps the
`visibility: list` models from `codex debug models`.

**Cross-check it against `codex debug models` first — that's free and authoritative.** It renders
the resolved model catalog as JSON, including `supported_reasoning_levels` and
`default_reasoning_level` per model, which reproduces most of this table without spending a call.
Use the paid sweep only to check where the catalog and the API actually disagree — and they do:

Four traps live in that table:

- **`gpt-6-astra` rejects `none`** — *"'none' is not supported with the 'gpt-6-astra' model. Supported values are: 'low', 'medium', 'high', 'xhigh', and 'max'."* Astra is the CLI's default model, so this is the easiest one to trip over.
- **The stderr header's `reasoning effort: none` means *unset*, not the `none` level.** A default astra run prints `reasoning effort: none` and succeeds, while passing `-c model_reasoning_effort=none` to that same model errors. Don't read the header as a valid value to echo back.
- **`max` is not universal** — `gpt-5.5` and `gpt-5.4-mini` top out at `xhigh`.
- **`ultra` is accepted more widely than it is advertised.** `codex debug models` enumerates it for `gpt-6-astra`, `gpt-5.6-sol` and `gpt-5.6-terra` only — yet a live call passes on `gpt-5.6-luna`, `gpt-5.5` and `gpt-5.4-mini` too, and the header echoes `reasoning effort: ultra`. It also never appears in the API's own rejection messages, which enumerate only `'none', 'low', 'medium', 'high', 'xhigh', and 'max'`. The catalog describes it as "maximum reasoning with automatic task delegation", which suggests it's resolved client-side rather than sent as a `reasoning.effort` value. Treat it as real where the catalog lists it, and don't rely on it doing something different from `max` where it doesn't.

**`minimal` is dead in practice, but for two different reasons.** On astra and the 5.6 family the API rejects the value outright. On `gpt-5.5` / `gpt-5.4-mini` the value still exists, and the call instead fails with *"The following tools cannot be used with reasoning.effort 'minimal': web_search."* — because web search is on by default. Either way: don't emit `minimal`.

**Defaults are per-model too.** `gpt-6-astra` and `gpt-5.6-sol` default to `low`; `gpt-5.6-terra`, `gpt-5.6-luna`, and `gpt-5.5` default to `medium`. Omitting `-c model_reasoning_effort` gives you the model's own default rather than a fixed `medium` — one more reason to omit it unless you're deliberately reaching for depth.

## Sandbox behaviour (verified)

Probed live on 0.153.4, because the flag names undersell what actually happens:

- **`read-only` really does block writes.** A write attempt fails with `patch rejected: writing is blocked by read-only sandbox; rejected by user approval settings` on stderr, and the file is not created.
- **`workspace-write` grants more than the workspace.** The run header reports its writable roots as `sandbox: workspace-write [workdir, /tmp, $TMPDIR]`. So `/tmp` is writable by default — if you're testing whether `--add-dir` works by targeting a directory under `/tmp`, you'll get a false pass. The roots are configurable via `-c sandbox_workspace_write.exclude_slash_tmp=true` / `.exclude_tmpdir_env_var=true`.
- **`--add-dir` genuinely extends the writable set** — with `/tmp` excluded, the same write is refused without it (`patch rejected: writing outside of the project`) and succeeds with it, and the added path shows up in the header's root list.
- **`-C, --cd <DIR>` overrides the shell's cwd**, and codex's own subshells run in that directory.
- **`--ephemeral` leaves no rollout file** — a normal run adds one file under `~/.codex/sessions/…`, an ephemeral run adds none, while still running normally.
- **`--approve-for-me` is not a milder `workspace-write`.** Its header reads `approval: on-request` + `sandbox: workspace-write [workdir, /tmp, $TMPDIR]`, and with `/tmp` excluded from the roots it *still* wrote outside the workspace — narrating "this requires elevated filesystem permission" and granting itself the escalation with no prompt. The identical run with `-s workspace-write` refused. And it is mutually exclusive with `-s/--sandbox`.

> ⚠️ **A denied write still exits 0.** Every sandbox refusal above returned exit status 0. The exit code tells you the *call* succeeded, not that the *edit* happened — verify against the filesystem.

> Side effect worth knowing: a `workspace-write` run appends `[projects."<workdir>"] trust_level = "trusted"` to `~/.codex/config.toml`. Codex modifies its own config outside the sandbox.

## Subcommands you may invoke

| Command | Purpose |
|---|---|
| `codex exec [PROMPT]` (alias `e`) | Non-interactive run — primary skill entry point |
| `codex exec resume [SESSION_ID] [PROMPT]` | Resume a previous session by UUID (a TUI-set thread name also works, but `exec`-created threads have only a UUID) |
| `codex exec resume --last [PROMPT]` | Resume most recent session |
| `codex exec review [PROMPT]` | Code review against the current repo, **scriptable** — has `-m`, `--json`, `-o`, `--skip-git-repo-check`. Prefer this one |
| `codex review [PROMPT]` | Same review, top-level. **No `-m`, no `--json`, no `-o`** as of 0.153.x — fine for a plain human-readable review, not for capture |
| `codex exec fork <SESSION_ID> [PROMPT]` | Branch a thread by UUID into a **new** session — non-interactive, so this is the one a skill uses. Verified: returns a fresh `thread_id` and inherits the parent's context |
| `codex fork` (top-level, interactive) | Picker-driven fork — drops into the TUI. Same name, wrong tool for scripted use |
| `codex resume` (top-level, interactive) | Picker-driven resume — drops into TUI |
| `codex agents` | Browse all agent sessions on the shared local app-server daemon (TUI) |
| `codex queue --thread <ID> --message <TEXT>` | Park a message on a thread without attaching to it. Works on **finished** sessions, not just live ones; the message is durable (stored in `~/.codex/queue_1.sqlite`) and is **delivered on that thread's next resume**. An unknown thread id exits 1 |
| `codex doctor` | Diagnose local install, config, auth, and runtime health (useful for pre-flight / debugging auth) |
| `codex archive` / `unarchive` / `delete` | Manage saved sessions by id or thread name |
| `codex migrate-rollouts` | Inspect (or `--apply`) migration of legacy sessions to paginated thread history |
| `codex login` / `codex logout` | OAuth credential management |
| `codex mcp` | Manage external MCP servers for codex |
| `codex sandbox` | Run arbitrary commands inside codex's sandbox (debug aid) |
| `codex apply` | Apply codex's last diff as `git apply` |
| `codex features list` | Inspect feature flags and their stage/state (names usable with `--enable`/`--disable`) |
| `codex update` | Self-update |

### `codex review` vs `codex exec review`

They run the same review, but the flag surfaces diverged. Top-level `codex review` takes only the scoping flags (`--uncommitted`, `--base`, `--commit`, `--title`) plus `-c` / `--enable` / `--disable` / `--strict-config`. `codex exec review` takes all of those **and** the exec-family flags — `-m`, `--json`, `-o`, `--skip-git-repo-check`, `--output-schema`, `--ephemeral`, `--thread-source`.

**None of the `exec` sub-subcommands take a sandbox.** `exec resume`, `exec review` and `exec fork` all lack `-s/--sandbox`, `-C/--cd` and `--add-dir` — only plain `codex exec` has them. For `resume` that's benign (it inherits the parent thread's sandbox), but the other two are worth care:

- `exec review` **creates** a thread, so there's nothing to inherit — it runs at whatever `~/.codex/config.toml` specifies. Don't describe it to the user as "read-only"; you haven't set it.
- `exec fork` inherits the parent's sandbox with no way to downgrade. Forking an image thread (created under `workspace-write`) silently carries write access forward, and `codex exec fork -s read-only` is a parse error, not an escape hatch.

So: use `codex review` when you just want the review printed, and `codex exec review` when you need to pick a model or capture the output to a file. Neither accepts `--skip-git-repo-check` meaningfully changing the requirement that you're in a repo — but top-level `codex review` *rejects the flag outright*, which is the drift this skill has been bitten by before.

## Session ids & resume (the `--json` schema)

To keep multiple Codex threads alive and resume the *exact* one later, capture each thread's id at creation.

**`codex exec --json` stdout** is JSONL using the `ThreadEvent` schema (unchanged in 0.153.4):

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
- **A plain run also prints the id on stderr**, in the run header (`session id: <UUID>`, alongside `model:` and `reasoning effort:`). Handy as a debug aid or a fallback, but `--json` stays the primary capture path — the event schema is a stable contract, while the header is human-readable output that can be reformatted at any time.
- The persisted **rollout file** (`~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<id>.jsonl`) uses a *different* shape — `{"type":"session_meta","payload":{"id":...}}`. Don't confuse it with the `--json` stdout stream.

## Common patterns

**One-shot, read-only review** (no `-m` / no effort — take the model's own defaults):
```bash
codex exec --sandbox read-only --skip-git-repo-check "review this function for race conditions" 2>/dev/null
```

**Reach for more depth on a genuinely hard task:**
```bash
codex exec -c model_reasoning_effort="high" --sandbox read-only --skip-git-repo-check "find the race in this scheduler" 2>/dev/null
```

**Pin a cheap model for a trivial side task:**
```bash
codex exec -m gpt-5.6-luna --sandbox read-only --skip-git-repo-check "list the TODOs in src/" 2>/dev/null
```

**Refactor with edits in workspace:**
```bash
codex exec --sandbox workspace-write --skip-git-repo-check "rename foo to bar across the repo" 2>/dev/null
```

**Let codex auto-review its own escalations** (note: no `--sandbox` — the two flags can't be combined, and this is *more* permissive than `workspace-write`, so treat it as an explicit-permission call):
```bash
codex exec --approve-for-me --skip-git-repo-check "apply the fix and run the tests" 2>/dev/null
```

**Full autonomy (only with explicit user OK):**
```bash
codex exec --sandbox danger-full-access --skip-git-repo-check "implement the spec in PLAN.md and run the tests" 2>/dev/null
```
> Deliberately no `-c model_reasoning_effort` here. `max` isn't valid on every model (`gpt-5.5` and `gpt-5.4-mini` cap at `xhigh`), so pinning it against an unpinned model can fail on the user's configured default — and provoking a retry loop is the last thing you want in the least-sandboxed command in this file.

**Long prompt via stdin:**
```bash
cat <<'EOF' | codex exec --sandbox read-only --skip-git-repo-check - 2>/dev/null
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
codex exec -m gpt-5.6-luna --sandbox read-only --skip-git-repo-check --json "list TODOs in src/, return JSON array of {file,line,text}" 2>/dev/null
```

**Force the answer into a JSON shape** — `--output-schema` takes a JSON Schema file, and `-o` then holds exactly conforming JSON (verified: a `{colour, count}` schema returned `{"colour":"blue","count":3}` and nothing else):
```bash
codex exec -m gpt-5.6-luna -c model_reasoning_effort="low" --sandbox read-only --skip-git-repo-check --output-schema /tmp/schema.json -o /tmp/out.json "<prompt>" 2>/dev/null
```
> Pair it with a fast model. One run of this on a high-effort model ran past 7 minutes and was killed, while the same call on `-m gpt-5.6-luna -c model_reasoning_effort=low` returned in seconds — a single observation, but enough reason not to leave structured output on a heavyweight default.

**Save only the final message to a file:**
```bash
codex exec --sandbox read-only --skip-git-repo-check -o /tmp/last.md "summarize CONTRIBUTING.md" 2>/dev/null
```

**Code review (current changes vs. default):**
```bash
codex review 2>/dev/null
```
> Target the review with: `--uncommitted` (staged + unstaged + untracked), `--base <branch>` (diff against a branch), `--commit <sha>` (one commit), and `--title <title>` for the summary header. Custom instructions go as the `[PROMPT]` positional (or via `-` on stdin). Top-level `codex review` does **not** accept `--skip-git-repo-check` (it operates on git changes, so a repo is required).

```bash
codex review --uncommitted 2>/dev/null
codex review --base main 2>/dev/null
```

**Review, captured to a file or on a chosen model** — use the `exec` form:
```bash
codex exec review --uncommitted --skip-git-repo-check -o /tmp/review.md 2>/dev/null
```

**Branch a thread instead of continuing it** — new thread id, parent context inherited:
```bash
codex exec fork --json --skip-git-repo-check <UUID> -o /tmp/ans.txt "<prompt>" 2>/dev/null > /tmp/fork-events.jsonl
```

**Park a message on a thread** for delivery on its next resume:
```bash
codex queue --thread <UUID> --message "also check the migration path"
```
> Prints `Queued message <id> for thread <UUID>.` and exits 0 (exit 1 on an unknown thread). Be careful pairing this with topic-aware sessions: a queued message is **durable and drains into the next `exec resume` of that thread**, so it turns up as an extra user turn in a later, possibly unrelated conversation. Verified: a queued `hello` produced a stray `Hello!` answer alongside the actual resume prompt's answer. Don't queue onto a thread you're also resuming normally.

**Validate a `-c` key before relying on it** — `--strict-config` turns an unknown key or bad value into an error instead of a silent no-op:
```bash
codex exec --strict-config -c web_search="live" --sandbox read-only --skip-git-repo-check "say OK" 2>/dev/null
```

## Verbatim `codex --help` (top-level)

```
Codex CLI

If no subcommand is specified, options will be forwarded to the interactive CLI.

Usage: codex [OPTIONS] [PROMPT]
       codex [OPTIONS] <COMMAND> [ARGS]

Commands:
  agents            Browse all agent sessions on the shared local app-server daemon
  exec              Run Codex non-interactively [aliases: e]
  review            Run a code review non-interactively
  login             Manage login
  logout            Remove stored authentication credentials
  mcp               Manage external MCP servers for Codex
  plugin            Manage Codex plugins
  mcp-server        Start Codex as an MCP server (stdio)
  app-server        [experimental] Run the app server or related tooling
  remote-control    [experimental] Manage the app-server daemon with remote control enabled
  app               Launch the Desktop app (opens the app installer if missing)
  completion        Generate shell completion scripts
  update            Update Codex to the latest version
  doctor            Diagnose local Codex installation, config, auth, and runtime health
  sandbox           Run commands within a Codex-provided sandbox
  debug             Debugging tools
  apply             Apply the latest diff produced by Codex agent as a `git apply` to your local
                    working tree [aliases: a]
  resume            Resume a previous interactive session (picker by default; use --last to continue
                    the most recent)
  queue             Queue a message for an existing session
  archive           Archive a saved session by id or session name
  delete            Permanently delete a saved session by id or session name
  migrate-rollouts  Inspect or migrate legacy local sessions to paginated thread history
  unarchive         Unarchive a saved session by id or session name
  fork              Fork a previous interactive session (picker by default; use --last to fork the
                    most recent)
  cloud             [EXPERIMENTAL] Browse tasks from Codex Cloud and apply changes locally
  exec-server       [EXPERIMENTAL] Run the standalone exec-server service
  features          Inspect feature flags
  help              Print this message or the help of the given subcommand(s)
```

(Full help body — including all options on `exec`, `exec resume`, and `exec review` — is captured in this skill's design notes; re-run `codex exec --help`, `codex exec resume --help`, and `codex exec review --help` if you need it verbatim again.)
