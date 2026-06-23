# sparkling-skills — maintainer notes

This repo is a **Claude Code marketplace** (`sparkling-skills`) that hosts plugins. Each plugin
is a purpose-grouped set of skills under `plugins/<name>/`. Today there's one:

- **`dispatch`** — delegate a task to an external AI CLI: `/codex` (OpenAI Codex) and `/agy`
  (Google Antigravity — multi-model: Gemini / Claude / GPT-OSS). `/gemini` is an alias that routes
  to `agy`. More plugins (e.g. diagrams, journeys) drop in as sibling folders later.

> **Gemini was retired (2026-06).** Google deprecated gemini-cli's free individual tier
> (`IneligibleTierError` → "migrate to Antigravity"), so the `gemini` skill was replaced by `agy`,
> which signs in with a free Google account and runs Gemini *and* Claude *and* GPT-OSS. The
> `/gemini` command still works — it routes through `agy` on a Gemini model.

## Layout
- `.claude-plugin/marketplace.json` — the marketplace catalog (lists each plugin).
- `plugins/<name>/.claude-plugin/plugin.json` — that plugin's manifest (metadata; skills
  auto-load from its `skills/`).
- `plugins/dispatch/skills/codex/`, `plugins/dispatch/skills/agy/` — each has `SKILL.md`,
  `references/flags.md`, and `evals/`. Their `/`-commands live in `plugins/dispatch/commands/`.
- `docs/PUBLISHING.md` — how to publish/update the marketplace. **Read before releasing.**
- `docs/research/` — full background research on Claude Code plugin/marketplace mechanics.

## Conventions (please follow)
- **Cross-platform.** Shipped skills must run on Windows/macOS/Linux. **No bash `.sh`** inside a
  skill — keep it pure markdown (Claude builds commands per-platform). Use **Python 3 stdlib**
  for dev tooling (e.g. the eval lints).
- **Run the eval lint before committing skill changes** — both must print "all N … valid":
  - `python3 plugins/dispatch/skills/codex/evals/lint_codex_commands.py`
  - `python3 plugins/dispatch/skills/agy/evals/lint_agy_commands.py`
- **Keep codex ↔ agy in lockstep where they overlap.** Shared core: topic-aware sessions, the
  delta "bridge", peer-evaluation, explicit-naming, optimistic pre-flight. But they differ by CLI,
  deliberately — codex has a read-only sandbox; **agy is agentic (no
  read-only mode) and multi-model**. Both generate images — codex's built-in imagegen, agy's
  native `generate_image` on the Google subscription. Don't blindly mirror.
- **Explicit-naming triggers.** Each skill fires only when its tool is named — codex; or agy /
  antigravity / gemini (all three route to agy). Keeps precision high. Descriptions are
  deliberately "pushy" to combat under-triggering; the `/codex` and `/agy` slash commands give a
  deterministic path.
- **Verify CLI/API facts against the live CLI or source — don't assume.** This repo has been
  bitten by stale/changed CLI facts (codex `web_search` enablement; gemini's deprecated tier;
  agy's cache-file session ids + its no-read-only behavior). When in doubt, run `<cli> --help` or
  read the CLI's source.

## Verified against
codex-cli **0.141.0**, agy (Antigravity) **1.0.10**. Re-verify and re-stamp `references/flags.md`
when bumping support (see each skill's `evals/README.md` checklist). agy is v1.0.x and moves
fast — expect flag churn.

## Claude Code plugin/marketplace docs
- Plugins — https://code.claude.com/docs/en/plugins
- Marketplaces — https://code.claude.com/docs/en/plugin-marketplaces
- Discover / install — https://code.claude.com/docs/en/discover-plugins
- Reference — https://code.claude.com/docs/en/plugins-reference
