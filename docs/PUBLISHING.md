# Publishing & maintaining the sparkling-skills marketplace

This repo is **both** a Claude Code marketplace and the plugin it serves. This doc covers how
to publish it and ship updates. For the underlying mechanics in depth (real-world examples,
full schemas), see [`research/`](./research/).

## How it's wired

- `.claude-plugin/marketplace.json` — the **marketplace** catalog at the repo root. Lists each
  plugin; today just `dispatch` with `"source": "./plugins/dispatch"`.
- `plugins/<name>/.claude-plugin/plugin.json` — each **plugin's** manifest (metadata only;
  skills auto-load from that plugin's `skills/`).
- `plugins/dispatch/skills/codex/`, `plugins/dispatch/skills/agy/` — the skills.

The repo root is the **storefront** (marketplace); each `plugins/<name>/` is an installable
**plugin** (a purpose-grouped set of skills). The marketplace `name` (`sparkling-skills`) is
what users type after `@`; the plugin `name` (`dispatch`) is what they install — both
independent of the GitHub repo slug.

## First-time publish

1. Create a **public** GitHub repo at `sparklingneuronics/sparkling-skills` (matches the
   `repository` URL in `plugin.json`).
2. Validate locally:
   ```
   claude plugin validate .
   ```
3. Push:
   ```
   git remote add origin git@github.com:sparklingneuronics/sparkling-skills.git
   git push -u origin main
   ```
4. Anyone can now install:
   ```
   /plugin marketplace add sparklingneuronics/sparkling-skills
   /plugin install dispatch@sparkling-skills
   ```

## Shipping updates — the version rule (important)

Version resolves from `plugin.json` `version` first. **Pitfall:** if you push new commits
without bumping `plugin.json`'s `version`, existing users get **no update**. So either:

- **Bump `plugin.json` `"version"`** (semver) on every release — explicit, recommended; or
- **Drop `version` from `plugin.json`** entirely → every commit becomes a new version (simplest
  for fast iteration).

Don't set `version` in **both** `plugin.json` and the marketplace entry — `plugin.json` wins
silently. The marketplace entry here intentionally omits `version`.

Before every release: run the eval lints (see [`../CLAUDE.md`](../CLAUDE.md)) and
`claude plugin validate .`.

## Adding more plugins

Each plugin is a purpose-grouped set of skills. To add one (say `c4-diagrams`), create
`plugins/c4-diagrams/.claude-plugin/plugin.json` + `plugins/c4-diagrams/skills/…`, then add an
entry to `marketplace.json` with `"source": "./plugins/c4-diagrams"`. Users install it with
`/plugin install c4-diagrams@sparkling-skills`. A plugin that outgrows the monorepo can switch
its entry from a relative `source` to a `github` source pointing at its own repo — the install
command doesn't change.

The `dispatch` plugin deliberately bundles the `codex` and `agy` skills (one purpose:
delegate to an external AI CLI). Group skills into a plugin by **purpose**, not one-per-plugin.

## Optional: team auto-install

A consuming repo's `.claude/settings.json` can declare `extraKnownMarketplaces` +
`enabledPlugins` to auto-prompt collaborators on trust. Not needed for public install.

## Links

- Plugins — https://code.claude.com/docs/en/plugins
- Marketplaces — https://code.claude.com/docs/en/plugin-marketplaces
- Discover / install — https://code.claude.com/docs/en/discover-plugins
- Reference — https://code.claude.com/docs/en/plugins-reference
- Full research — [`research/01-official-mechanics.md`](./research/01-official-mechanics.md),
  [`research/02-real-examples-and-repo-fit.md`](./research/02-real-examples-and-repo-fit.md)
