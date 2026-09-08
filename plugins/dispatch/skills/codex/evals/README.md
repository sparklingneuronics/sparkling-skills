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
| 3 | **Capability probe** (`probe_codex_capabilities.py`) | *Semantic* drift — flags that are individually valid but can't be combined, value sets that gained/lost a variant, model×effort pairs the API refuses | tier 1 ~2s free; tier 2 paid | `codex` on PATH + auth (tier 2) |
| 4 | **Behavior probe** (`probe_skill_behavior.py` + `fake_codex.py`) | The *judgment* layer — topic routing, sandbox selection, the codex↔agy boundary. Asserts on the argv the skill actually builds | Claude tokens; **no** codex/OpenAI usage | `claude` CLI |

Eval 1 is the highest-value one: CLI drift is the demonstrated failure mode
(the skill once shipped `codex review --skip-git-repo-check`, which a CLI
upgrade turned into an error). It's nearly free, so run it on every change.

We deliberately skip a full output-quality benchmark — grading codex's prose
isn't grading this skill. The *safety decisions* (does a write request pick
`workspace-write`? does it escalate further without consent?) are covered by
eval 4 instead, which asserts on the command the skill builds rather than the
answer it gets back.

The **topic-aware session logic** (infer the topic → match/resume the right
thread → build the bridge) is judgment, not a deterministic command shape, so
no lint can see it: eval 1 only checks that the `--json` / `resume <UUID>`
command *shapes* are valid, not that the *right* thread was chosen. Eval 4
covers the routing decision by replaying a scripted two-turn conversation
against a fake `codex` and checking which id the follow-up resumed. The
*content* of the bridge summary remains unjudged — that one really is taste.

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
  the CLI only accepts `disabled`/`cached`/`indexed`/`live`. (Note: `--enable
  web_search` itself is *accepted-but-deprecated* on 0.153.4, not an error.)
  Feature/config *values* are a source/CLI check, not a lint check. Handy trick:
  `--strict-config` turns an unknown `-c` key or bad value into a hard error, so
  `codex exec --strict-config -c <key>=<value> …` is a cheap way to verify one.
- It can't verify **model names** (`gpt-5.6-luna`, …) — the CLI doesn't
  enumerate them in `--help`. Those are checked by hand; see the model table in
  `references/flags.md`, which records live probe results per model. This is
  also why the skill omits `-m` on routine calls — an unpinned model can't rot.
  The authoritative lineup comes from **`codex debug models`**, which renders the
  resolved catalog as JSON (slug, `visibility`, `default_reasoning_level`,
  `supported_reasoning_levels`) for free and offline. Don't scrape the binary:
  it carries a *bundled* preset blob that disagrees with what the CLI actually
  resolves — it still lists `gpt-5.2`, which the catalog does not carry, and
  marks `gpt-5.4-mini` hidden when it is listed.
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

## Eval 3 — capability probe

Eval 1 answers "does this flag exist?". Eval 3 answers "does it actually work,
and does it work *here*?" — the gap that produced every runtime failure this
skill has shipped.

```bash
python3 evals/probe_codex_capabilities.py                     # tier 1 only (free, ~2s)
python3 evals/probe_codex_capabilities.py --matrix            # + paid sweep
python3 evals/probe_codex_capabilities.py --matrix --markdown # emit the flags.md table
```

**Tier 1 — invariants (free).** Everything here resolves at argument-parse or
config-load time, so no API call is made and nothing is billed. Run it as
freely as the lint. It asserts the documented mutual exclusions (`exec` rejects
`-a` and `--search`; `--approve-for-me` cannot be combined with `--sandbox`;
top-level `review` rejects `--skip-git-repo-check`), the `review` ↔ `exec
review` flag split, and — the useful trick — it *derives* the legal value sets
for `--sandbox` and `web_search` by feeding the CLI a bogus value and parsing
its own rejection message. That turns "OpenAI added a `web_search` mode" from a
silent doc rot into a failing check.

**Tier 2 — model × effort matrix (paid, opt-in).** One real `codex exec` per
cell, run in parallel, printing the markdown table that lives in the
*Reasoning effort* section of `references/flags.md`. Models are discovered from
`codex debug models` (the CLI's own resolved catalog), so a newly
shipped model joins the sweep without editing this file. Budget one trivial
call per cell — the current lineup is ~48.

This tier is what caught: `gpt-6-astra` rejecting `none` (on the *default*
model), `gpt-5.4-mini` rejecting `max`, `ultra` being accepted everywhere while
appearing in no API enumeration, and `minimal` failing for two different
reasons depending on the model.

**Don't wire tier 2 into pre-commit** — it costs real money and needs auth. It's
a release-time / CLI-upgrade check. Tier 1 is cheap enough to run beside the lint.

---

## Eval 4 — behavior probe (the judgment layer)

Evals 1 and 3 interrogate the CLI. Neither one runs the skill. This one does —
it's the "fake `codex` that logs argv" tier this README used to describe as a
to-do.

```bash
python3 evals/probe_skill_behavior.py               # all scenarios
python3 evals/probe_skill_behavior.py -k resume     # just the matching ones
python3 evals/probe_skill_behavior.py --keep        # keep scratch dirs to inspect
python3 evals/probe_skill_behavior.py --workers 1   # serial, easier to debug
```

`fake_codex.py` goes on `PATH` as `codex`. It records every invocation as JSON
and returns just enough well-formed output to keep the documented flow alive —
a `thread.started` event on `--json` (with a deterministic id), an answer
written to `-o`, a run header on stderr, exit 0. That fidelity matters: the
skill captures a thread id and resumes it later, so a fake that didn't hand
back a usable id couldn't test whether the *right* thread gets resumed.

The runner hands `SKILL.md` to a headless `claude -p`, plays a scripted
conversation (multi-turn via `--resume`), and asserts on the recorded argv.

What the scenarios lock down:

| Scenario | Guards |
|---|---|
| `routine-readonly` | the default posture — `read-only`, `--skip-git-repo-check`, and **no pinned `-m`** (the omit-the-model decision) |
| `resume-same-topic` | a follow-up resumes the **stored UUID**, never `--last` |
| `new-topic-fresh-thread` | an unrelated request starts a fresh thread instead of cross-contaminating |
| `write-picks-workspace-write` | an edit request escalates to `workspace-write` — and no further |
| `review-variant` | uses the review subcommand, scoped `--uncommitted`, and never passes `--skip-git-repo-check` to top-level `review` (the regression this skill once shipped) |
| `negative-gemini` | naming gemini/agy invokes **no** codex call at all |

**No codex or OpenAI usage** — the fake absorbs it all, so the safety assertions
are free to re-run. It does spend Claude tokens (one headless turn per
conversation turn), so it's opt-in rather than a pre-commit hook.

Add a scenario whenever you change the routing or safety rules — those are
exactly the parts no lint can see.

### Writing a scenario that tests what you think it tests

Three traps, each of which produced a false failure while building this:

- **Give the scenario something real to act on.** `seed_workspace()` lays down a
  git repo with a committed `calc.py` and an uncommitted edit. In an empty
  directory the skill correctly *declines* to delegate "rename `load` everywhere"
  — good judgment that reads as a failed assertion.
- **Don't lie to the skill.** A turn saying "I rewrote it to use a context
  manager" against an unmodified file gets caught: the skill checks `git diff`
  and mtime, sees the claim is false, and refuses to send a misleading bridge to
  codex — which is precisely what `SKILL.md` asks of it. Use a turn's `before`
  hook to make the claim true before asserting on the resume path.
- **Re-append the skill on every turn.** `--resume` restores conversation
  history but *not* `--append-system-prompt`, so a resumed turn otherwise runs
  with no skill loaded — the eval would pass turn 1 and silently measure nothing
  afterwards.

Also note the probe filters out `codex <sub> --help` invocations. Claude
sometimes checks syntax before committing to a real call; counting that as the
delegation makes the next assertion inspect the wrong command.

### What this eval cannot tell you

`fake_codex.py` returns a fixed canned answer, so it can verify *which command
was built* but never *whether the exchange was useful*. That has one observable
side effect worth knowing: when the canned reply obviously doesn't match the
question (a code-review answer to an email-tone question), the skill sometimes
notices and probes codex with a throwaway prompt to check it's working. That's
reasonable behavior, and harmless here, but it means call counts can include a
diagnostic call the scenario didn't ask for — assert on the *shape* of calls
(subcommand, sandbox, resumed id) rather than on an exact count.

Judging answer quality is deliberately out of scope: that would be grading
codex, which is the benchmark this eval suite exists to avoid.

---

## When you update the skill — the checklist

1. **Make your edits** to `SKILL.md` / `references/flags.md`.
2. **Run the lint** — `python3 evals/lint_codex_commands.py`. Green before commit.
   Run **eval 3 tier 1** too (`probe_codex_capabilities.py`) — same cost, catches
   a different class.
3. **If you bumped the supported codex version** (or either check flags drift):
   run `probe_codex_capabilities.py --matrix --markdown` and paste the refreshed
   effort table into `references/flags.md`, then re-capture the CLI surface —
   ```bash
   codex --version
   codex --help; codex exec --help; codex exec resume --help
   codex review --help; codex exec review --help
   codex features list
   ```
   update the version stamp at the top of `flags.md`, fix any changed
   flags/subcommands, then re-run the lint until clean.
4. **If you changed `description:`** (the trigger), run eval 2 and confirm the
   held-out trigger score didn't regress.
5. **If you added a new command pattern** the lint should know about (a new
   value-taking flag, a new subcommand), update `VALUE_FLAGS` / `SUBCOMMANDS`
   in `lint_codex_commands.py` so it parses correctly.
6. **If you touched the routing or safety rules** — default sandbox, when to
   resume vs. start fresh, the codex↔agy boundary — run **eval 4**
   (`probe_skill_behavior.py`). It costs no codex usage, and it's the only check
   that sees whether the skill *acts* the way the prose claims.

---

## Parameterizing across skills

Evals 1 and 2 are the same shape for the sibling `agy` skill (which replaced the
retired `gemini` skill). `agy` already ships its own `lint_agy_commands.py` +
`trigger_cases.json`, so the sibling lints duplicate the help-parser logic. A
future cleanup could generalize them into one parameterized lint (CLI name +
subcommand/value-flag sets + help layout) with one `trigger_cases.json` per
skill, instead of forks.

Evals 3 and 4 are **codex-only so far**, and both would port cheaply:

- **Eval 3** is mostly CLI-specific assertions, but the useful trick generalizes
  — feed a flag a bogus value and parse the CLI's own "expected one of …"
  rejection to derive the legal set. `agy` is v1.0.x and churns fast, so the
  same drift risk applies.
- **Eval 4** is almost entirely reusable. `fake_codex.py` would become
  `fake_agy.py` (different argv shape and session-id mechanism — agy uses cache
  files rather than a `thread.started` event), while the runner, the `Call`
  parser, and the scenario/assertion structure carry over unchanged. The
  scenarios worth keeping are the boundary ones: naming codex must **not**
  invoke agy, which is the mirror of `negative-gemini` here.
