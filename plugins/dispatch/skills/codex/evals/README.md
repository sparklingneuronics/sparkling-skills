# Evals for the `codex` skill

How this skill is tested, how to run the tests, and what to do when you update
the skill. Read this before changing `SKILL.md` or `references/flags.md`.

These files are **developer/CI tooling**. They are not loaded into Claude's
context at runtime and don't ship as part of the skill's behavior — they only
exist to keep the skill honest across edits and codex-CLI upgrades.

---

## Why these evals (and not the usual benchmark loop)

The standard skill-creator loop runs a skill for real and grades the artifact.
That fits poorly here, because this skill's "artifact" is a call to the live
`codex` CLI, which is **OAuth-gated, networked, paid, non-deterministic, and
slow** — and what you'd be grading is *codex's* answer quality, not the skill's.
The skill's actual job ends when it (a) fires on the right request and (b)
constructs a correct, correctly-flagged command with the right safety posture.

So we test those two things directly, cheaply, and deterministically:

| # | Eval | What it guards | Cost | Needs |
|---|------|----------------|------|-------|
| 1 | **Command-parse lint** (`lint_codex_commands.py`) | CLI drift — a documented command using a flag/subcommand the installed CLI no longer accepts | ~1s, offline | `codex` on PATH |
| 2 | **Trigger cases** (`trigger_cases.json`) | Mis-firing — skill triggering on near-misses (e.g. `gemini`, image-gen, "do it yourself") or failing to trigger when it should | LLM loop | skill-creator + `claude` CLI |

Eval 1 is the highest-value one: CLI drift is the demonstrated failure mode
(the skill once shipped `codex review --skip-git-repo-check`, which a CLI
upgrade turned into an error). It's nearly free, so run it on every change.

We deliberately skip a full output-quality benchmark. If you ever want to guard
the *safety decisions* too (does a write request pick `workspace-write` and
confirm first? does it refuse `danger-full-access` without consent?), see
"Adding command-construction evals" below — that's the natural third tier.

The **topic-aware session logic** (infer the topic → match/resume the right
thread → build the bridge) is judgment, not a deterministic command shape, so it
isn't unit-tested here either — the lint only checks that the `--json` /
`resume <UUID>` command *shapes* are valid. Guarding the routing/bridge behavior
belongs to that same command-construction tier (a fake `codex` that logs argv).

---

## Eval 1 — command-parse lint

`lint_codex_commands.py` pulls every `codex …` command out of the fenced code
blocks in `SKILL.md` and `references/flags.md`, works out each command's
subcommand path and flags, and checks them against the installed CLI's own
`codex <subcommand> --help`. Anything the CLI would reject is reported.

### Run it

```bash
python3 evals/lint_codex_commands.py            # pass/fail summary
python3 evals/lint_codex_commands.py --verbose  # show every command checked
python3 evals/lint_codex_commands.py --skill /path/to/skill   # lint another copy
```

Exit codes: `0` clean · `1` drift found · `2` couldn't validate (`codex` not on
PATH). The `1`/`2` split makes it CI-friendly.

### Reading a failure

A failure looks like this (the real regression this skill once shipped):

```
✗ SKILL.md:NN: `codex review` rejects --skip-git-repo-check
        codex review --skip-git-repo-check 2>/dev/null
```

It means the cited command uses `--skip-git-repo-check`, but `codex review
--help` on the installed CLI doesn't list it. Either the flag moved/was removed,
or the doc was wrong. Fix the command and re-run. (`NN` is whatever line the
offending command sits at — it shifts as the file changes.)

### How it decides what's valid

For each command it runs `codex <chain> --help` once (cached) and parses the
option lines into a valid-flag set. Per-subcommand help already includes the
parent flags that are legal at that level (e.g. `codex exec resume --help`
lists `--skip-git-repo-check`), so checking against the deepest chain's help is
correct. Flag *values* (`-m gpt-5.5`, `--sandbox read-only`) and placeholders
(`<prompt>`, `-` for stdin) are skipped; `-h/--help/-V/--version` are always OK.

### Limitations (know these before trusting a green run)

- It validates **flag and subcommand names**, not semantics. `--base` with a
  bad branch, or a wrong `-c key`/value, still passes — e.g. `--enable
  some_unknown_feature` *looks* fine to the lint (`--enable` is a real flag and
  the feature name is consumed as its value) but errors at runtime
  (`Unknown feature flag`). Likewise `-c web_search="on"` passes the lint though
  the CLI only accepts `live`/`cached`/`disabled`. (Note: `--enable web_search`
  itself is *accepted-but-deprecated* on 0.141.0, not an error.) Feature/config
  *values* are a source/CLI check, not a lint check.
- It can't verify **model names** (`gpt-5.5`, …) — the CLI doesn't enumerate
  them. Those are checked by hand against OpenAI's lineup; see eval-2 notes and
  the model list in `references/flags.md`.
- It only reads fenced code blocks. Commands mentioned in prose or tables
  aren't linted (intentional — they're not runnable).

---

## Eval 2 — trigger cases

`trigger_cases.json` is the should-/shouldn't-trigger set. The valuable cases
are the **near-misses**: `ask gemini to review this` (routes to the sibling
`agy` skill, not codex), `generate an image…`, `just write it yourself`,
`explain how the codex CLI works` (a question *about* codex, not a delegation).
The codex↔agy boundary — any request naming agy / antigravity / gemini — is the
real risk; keep both sides represented.

Schema (the format skill-creator's optimizer expects):

```json
[ {"query": "…", "should_trigger": true}, {"query": "…", "should_trigger": false} ]
```

### Run it (description optimization)

The trigger of a skill is driven entirely by its `description:` frontmatter.
skill-creator ships a loop that scores the description against these cases and
proposes improvements. From the skill-creator skill directory:

```bash
python -m scripts.run_loop \
  --eval-set  /abs/path/to/skills/codex/evals/trigger_cases.json \
  --skill-path /abs/path/to/skills/codex \
  --model <the-claude-model-id-powering-your-session> \
  --max-iterations 5 --verbose
```

It splits the set 60/40 train/test, evaluates the current description (3 runs
per query for a stable trigger rate), proposes a better description, and picks
the winner by **test** score (not train) to avoid overfitting. Apply the
resulting `best_description` to `SKILL.md`'s frontmatter only if it beats the
current one on the held-out set.

### Add a case whenever

…you notice the skill firing when it shouldn't (add it as `false`) or missing a
request it should own (add it as `true`). New near-misses are worth more than
new obvious cases — aim the set at the boundary, not the easy middle.

---

## When you update the skill — the checklist

1. **Make your edits** to `SKILL.md` / `references/flags.md`.
2. **Run the lint** — `python3 evals/lint_codex_commands.py`. Green before commit.
3. **If you bumped the supported codex version** (or the lint flags drift):
   re-capture the CLI surface and update `references/flags.md` to match —
   ```bash
   codex --version
   codex --help; codex exec --help; codex exec resume --help; codex review --help
   ```
   update the version stamp at the top of `flags.md`, fix any changed
   flags/subcommands, then re-run the lint until clean.
4. **If you changed `description:`** (the trigger), run eval 2 and confirm the
   held-out trigger score didn't regress.
5. **If you added a new command pattern** the lint should know about (a new
   value-taking flag, a new subcommand), update `VALUE_FLAGS` / `SUBCOMMANDS`
   in `lint_codex_commands.py` so it parses correctly.

---

## Adding command-construction evals (optional third tier)

To guard the safety posture (not just flag names), test that a *request*
produces the right command without hitting the network: put a fake `codex` on
PATH that just logs its `argv` and exits 0, run the skill against prompts like
"rename foo to bar across the repo" (expect `--sandbox workspace-write` **and**
a confirmation first) or "review my uncommitted changes" (expect
`codex review --uncommitted`, never `--skip-git-repo-check`), then assert on the
logged argv. More setup than evals 1–2 — add it when the safety rules are worth
locking down.

---

## Parameterizing across skills

Evals 1 and 2 are the same shape for the sibling `agy` skill (which replaced the
retired `gemini` skill). `agy` already ships its own `lint_agy_commands.py` +
`trigger_cases.json`, so three sibling lints now share the help-parser logic. A
future cleanup could generalize them into one parameterized lint (CLI name +
subcommand/value-flag sets + help layout) with one `trigger_cases.json` per
skill, instead of three forks.
