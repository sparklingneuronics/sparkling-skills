# `agy` (Antigravity CLI) reference

Verified against **agy 1.0.10** (`agy --version`). agy is brand-new and moving fast — the help is the source of truth at runtime; re-check with `agy --help` if behavior surprises you.

## Top-level flags

`agy --help` (Go-flag format — note the single-dash long flags work too):

| Flag | Meaning |
|------|---------|
| `-p`, `--print`, `--prompt` | Run a single prompt **non-interactively** and print the response. The delegation entry point. |
| `-i`, `--prompt-interactive` | Run an initial prompt, then continue interactively (not for delegation). |
| `--model <display string>` | Model for this session. Verbatim string from `agy models` (see below). |
| `-c`, `--continue` | Continue the **most recent** conversation. |
| `--conversation <id>` | Resume a **specific** conversation by its UUID. Cwd-independent — the reliable resume. |
| `--add-dir <dir>` | Add a directory to the workspace (repeatable). |
| `--dangerously-skip-permissions` | Auto-approve all tool-permission requests. In headless `-p` this is effectively already the default. |
| `--sandbox` | Run with terminal restrictions (network / out-of-workspace). **Not** a read-only mode — local writes still happen. |
| `--print-timeout <dur>` | Timeout for `-p` wait. Default **5m0s**. |
| `--log-file <path>` | Override the CLI log path (logs default to `~/.gemini/antigravity-cli/log/`). |

There is **no** `--json` / `-o` / `--output` / `--format` flag — output is plain stdout only.

## Subcommands

- `agy models` — list available models (no flags).
- `agy plugin <cmd>` (alias `plugins`): `list`, `import [gemini|claude]`, `install <target>` (e.g. `name@marketplace`), `uninstall <name>`, `enable <name>`, `disable <name>`, `validate [path]`, `link <mp> <target>`, `help`. (Importing the `nanobanana` extension is optional — agy generates images natively; see Images below.)
- `agy install` — configure PATH / shell aliases (`--dir`, `--skip-aliases`, `--skip-path`).
- `agy changelog` — release notes.
- `agy update` — update the CLI.
- `agy help [subcommand]` — help (subcommands also take `-h`/`--help`).

## Models

`agy models` (this account, agy 1.0.10):

```
Gemini 3.5 Flash (Medium) | (High) | (Low)
Gemini 3.1 Pro (Low) | (High)
Claude Sonnet 4.6 (Thinking)
Claude Opus 4.6 (Thinking)
GPT-OSS 120B (Medium)
```

- **Default** (no `--model`): the **Gemini 3.5 Flash** family, reached by *omitting* `--model`. The bare string `Gemini 3.5 Flash` is **not** a selectable `agy models` entry (only the tiered variants are) — don't pass it; it'd be silently ignored.
- `--model` takes the **verbatim display string**, e.g. `--model "Gemini 3.1 Pro (High)"`. The `(Low/Medium/High/Thinking)` suffix is a **reasoning-effort tier**, not a separate model.
- **An unknown `--model` is silently ignored** — agy falls back to the default with no error. So only pass strings that appear in `agy models`; don't rely on agy to reject a typo.
- Selecting a **Claude** or **GPT-OSS** model routes to that provider **through Google's Antigravity backend** (Google-brokered, billed against Google's quota/credits — not your own Anthropic/OpenAI key).

## Conversations & resume (the id mechanism)

- No id is printed to stdout/stderr and you can't set one (no `--session-id` like gemini).
- State lives under **`~/.gemini/antigravity-cli/`**:
  - `conversations/<UUID>.db` — one SQLite DB per conversation. Ids are standard UUIDs.
  - **`cache/last_conversations.json`** — maps each **workspace dir → its latest conversation UUID**. Rewritten after every `-p` run for that cwd. **This is the capture point**: read the value for the current dir right after a call.
  - `history.jsonl` — prompt log (no ids).
- **Resume by id:** `agy --conversation <uuid> -p "<prompt>"` — cwd-independent, the reliable path.
- **`-c` / `--continue`** resumes the latest conversation. From the matching workspace it's instant; from a different/empty dir it resorts to agentically grepping transcripts to find one — slow and side-effecty. Prefer `--conversation <uuid>` for topic routing.

## Safety / permissions

- **No read-only mode.** Headless `agy -p` auto-approves and executes tools — it will create/modify files and run shell if the task leads there (verified: it wrote a file with no `--dangerously-skip-permissions`).
- `--sandbox` gates network / full-disk / out-of-workspace operations behind confirmation, but **did not block a local `/tmp` write** — treat it as "restrict escape", not "read-only".
- For read-only intent, constrain via the **prompt** ("analyze and answer only; don't modify files or run shell") and/or scope the workspace (`--add-dir` / cwd).

## Gotchas

- **Cold start ~2–3 min** on the first call (language-server spin-up + auth). Use a generous timeout; `--print-timeout` defaults to 5m.
- **Non-TTY stdout drop** ([antigravity-cli#76](https://github.com/google-antigravity/antigravity-cli/issues/76)): on some builds (v1.0.0 / Windows), `agy -p` can exit 0 with **empty** piped stdout. Not reproduced on macOS 1.0.10, but guard for it: empty output + exit 0 → retry once.
- **Shared `~/.gemini/` lineage** — agy reuses gemini-cli's config/auth dir (`oauth_creds.json`, `settings.json`, plugins). Per-model settings live in `~/.gemini/antigravity-cli/settings.json` and interactive use can mutate them under a script.
- **Images**: agy generates images **natively** via a built-in `generate_image` tool (Antigravity's Nano Banana Pro model), on the Google subscription — no API key or extension. Just ask in a `-p` call ("generate … and save to `<path>`"); it honors the path. (The `nanobanana` gemini-cli extension on disk is unregistered and unnecessary — an API-key path you don't need.)
- **Auth** = free Google account OAuth ("oauth-personal"); the sanctioned successor to gemini-cli's deprecated individual tier. No API key. `/logout` (interactive) signs out.
- **Per-model quotas** exist (premium Gemini-Pro / Claude buckets) and aren't publicly numbered — they can exhaust; fall back to a lighter model.

## Docs

- Antigravity — https://antigravity.google
- CLI repo (issues / README; proprietary) — https://github.com/google-antigravity/antigravity-cli
- Gemini-CLI → Antigravity migration — https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/
