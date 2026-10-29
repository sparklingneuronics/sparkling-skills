# Changelog

Notable changes to the `dispatch` plugin. Version numbers are the `version` in
`plugins/dispatch/.claude-plugin/plugin.json`, which is what decides whether existing users get an
update (see [docs/PUBLISHING.md](docs/PUBLISHING.md)). The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Each entry lists the CLI versions the skills were verified against.

## [1.4.0] - 2026-10-29

Verified against codex-cli 0.165.0 and agy 1.0.10.

### Changed
- codex: the reference now lists `gpt-6.1-sol` as codex's default model (it was `gpt-6-astra`).
  The skill doesn't pin a model, so routine calls are unaffected.
- codex: model table refreshed. New: `gpt-6.1-sol`, `gpt-6.1-terra`, `gpt-6-sol`, `gpt-6-luna`.
  `gpt-5.5` and `gpt-5.4-mini` are now rejected on ChatGPT sign-in.
- codex: reasoning-effort table regenerated from a live probe of every model. `max` and `ultra`
  work on every current model, `none` is rejected by `gpt-6.1-sol` and `gpt-6-astra`, and
  `minimal` fails everywhere.
- codex: cheap-model examples use `gpt-6-luna` instead of `gpt-5.6-luna`.
- codex: transparent image backgrounds now work, so the skill asks for one directly instead of
  suggesting a workaround.

### Added
- codex: `--worktree`, documented as opt-in for write tasks. Codex works in a new git worktree
  checked out from the last commit, so it doesn't see uncommitted changes, and the worktree is
  left behind afterwards.
- codex: reference entries for `--cyber-access-program`, `--no-daemon` and `migrate-nfs-db`.

### Removed
- codex: `codex mcp-server` from the reference. The CLI removed it in 0.154.0.

## [1.3.0] - 2026-09-08

Verified against codex-cli 0.153.4 and agy 1.0.10.
([PR #1](https://github.com/sparklingneuronics/sparkling-skills/pull/1))

### Changed
- codex: routine calls no longer pin a model or reasoning effort, so codex uses whatever the
  user's install considers current. The `/codex` command had its own "default to gpt-5.5"
  instruction; that's gone too.
- codex: `--approve-for-me` is now treated like `danger-full-access` (explicit permission only).
  It auto-approves escalations outside the workspace, so it is more permissive than
  `workspace-write`, and it can't be combined with `--sandbox`.
- codex: reference updated for 0.153.4: `gpt-6-astra` as the default, a per-model effort table,
  web search's `indexed` mode, `-a` without `untrusted`, and `workspace-write` also covering
  `/tmp` and `$TMPDIR`.

### Fixed
- codex: a write blocked by the sandbox still exits 0, so error handling no longer treats exit 0
  as proof that an edit happened.
- codex: documented that top-level `codex fork` is the interactive picker and `codex exec fork`
  is the scriptable one.

### Added
- codex evals: a capability probe (free invariant checks plus an opt-in, paid model × effort
  sweep) and a behavior probe that runs the skill against a fake `codex` and checks the commands
  it builds.
- codex evals: the lint now catches unknown subcommands. Before, they passed because codex
  prints the parent command's help.

## [1.2.0] - 2026-07-11

Verified against codex-cli 0.144.1 and agy 1.0.10.

### Changed
- codex: updated for codex-cli 0.144.1 and the GPT-5.6 models. The skill's default model became
  `gpt-5.6-terra` (was `gpt-5.5`), with `gpt-5.6-luna` added. `gpt-5.6-sol` and bare `gpt-5.6`
  were noted as not yet available on ChatGPT sign-in. Added the `max` effort level, and `--search`
  is documented as a top-level flag (it was TUI-only).
- agy: skill description shortened from 1219 to 993 characters to fit the 1024-character limit
  in the agentskills.io spec. All trigger phrases kept.

### Added
- Discovery keywords in `plugin.json`.

## [1.1.0] - 2026-06-23

First public release. Verified against codex-cli 0.141.0 and agy 1.0.10.

- The `dispatch` plugin with two skills: `codex` (OpenAI Codex CLI) and `agy` (Google
  Antigravity CLI, which runs Gemini, Claude and GPT-OSS models), plus the `/codex`, `/agy` and
  `/gemini` commands.
- Each skill triggers only when its tool is named. Within a conversation it keeps a separate
  thread per topic and resumes it with a short summary of what changed since.
- Image generation through either tool, again only when the tool is named.
- Eval lints that check every documented command against the installed CLI.

Version 1.0.0 predates the public history. It had a `gemini-cli` skill, which was replaced by
`agy` after Google deprecated gemini-cli's free tier. `/gemini` now routes to `agy` on a Gemini
model.
