# Evals for the `agy` skill

How this skill is tested, how to run the tests, and what to do when you update
the skill. Read this before changing `SKILL.md` or `references/flags.md`.

These files are **developer/CI tooling** — not loaded into Claude's context at
runtime. They keep the skill honest across edits and agy upgrades. The sibling
`codex` skill has the same setup; this is its mirror, adapted to the
Antigravity CLI's reality.

---

## Why these evals (and not the usual benchmark loop)

The standard skill-creator loop runs a skill for real and grades the artifact.
That fits poorly here: the "artifact" is a call to the live `agy` CLI —
**account-gated, networked, metered, non-deterministic, and slow (cold start
2–3 min)** — and you'd be grading *agy's* answer, not the skill's. The skill's
job ends when it (a) fires on the right request and (b) builds a correct,
correctly-flagged command. So we test those, cheaply and deterministically:

| # | Eval | What it guards | Cost | Needs |
|---|------|----------------|------|-------|
| 1 | **Command-parse lint** (`lint_agy_commands.py`) | CLI drift — a documented command using a flag/subcommand the installed CLI no longer accepts | ~1s, offline | `agy` on PATH |
| 2 | **Trigger cases** (`trigger_cases.json`) | Mis-firing — triggering on near-misses (codex, bare image, "Gemini the zodiac sign", "anti-gravity" the physics) or failing to fire when agy/antigravity/gemini is named | LLM loop | skill-creator + `claude` CLI |

Run eval 1 on every change — agy is **v1.0.x and moves fast** (near-daily
releases), so flag/subcommand drift is the most likely breakage.

---

## Eval 1 — command-parse lint

`lint_agy_commands.py` pulls every `agy …` command from the fenced code blocks
in `SKILL.md` and `references/flags.md`, works out each command's subcommand
path and flags, and checks them against the installed CLI's own
`agy <subcommand> --help`. Anything the CLI would reject is reported.

It is the codex/gemini lint adapted for agy. The help-flag parser is shared —
it now handles **three** layouts: clap (codex), yargs (gemini), and **Go-flag**
(agy: `Usage of agy:` with one `--flag   description` per line). The CLI name,
`SUBCOMMANDS`, `VALUE_FLAGS`, and the help-output markers are agy-specific.

### Run it

```bash
python3 evals/lint_agy_commands.py            # pass/fail summary
python3 evals/lint_agy_commands.py --verbose  # show every command checked
```

Exit codes: `0` clean · `1` drift · `2` couldn't validate (`agy` not on PATH).

### Limitations (know these before trusting a green run)

- Validates **flag/subcommand names**, not semantics or behavior. The lint can't
  see that `agy -p` is **not read-only** (it auto-runs tools), that `--sandbox`
  doesn't block local writes, or that an **unknown `--model` is silently
  ignored** — all runtime behavior, not flags.
- Can't verify **model strings** (`Gemini 3.1 Pro (High)`, `Claude Opus 4.6
  (Thinking)`, …). agy *accepts anything* and falls back to default on a typo, so
  there's no error to catch — check by hand against `agy models` /
  `references/flags.md`.
- Can't see the **cache-file session mechanism** or the **empty-stdout (#76)**
  failure mode — those are the smoke tests below.
- Only reads fenced code blocks; prose/table mentions aren't linted.

---

## Eval 2 — trigger cases

`trigger_cases.json` is the should-/shouldn't-trigger set. The valuable cases
are the **near-misses**, and agy's span three tools and two homonyms:

- **codex↔agy boundary** — "ask **codex** to review this" must NOT fire agy.
- **the gemini takeover** — "ask **gemini** …" / "validate with **gemini**"
  *should* fire agy now (gemini-cli's individual tier is retired; agy is the
  successor running a Gemini model).
- **bare image / no tool named** — "create an image", "review my PR" with no tool
  named must NOT auto-route to agy (the user picks by naming a tool). agy *does*
  generate images, but only on an explicit "use agy to make an image" request.
- **the homonyms** — "my partner is a **Gemini** (zodiac)" and "does
  **anti-gravity** exist in physics" must NOT fire.
- **about/install vs delegation** — "explain antigravity's permission model" and
  "help me install Antigravity / sign in" are *about* agy, not delegations *to*
  it.

Run it via skill-creator's description optimizer (same as codex/gemini):

```bash
python -m scripts.run_loop \
  --eval-set  /abs/path/to/skills/agy/evals/trigger_cases.json \
  --skill-path /abs/path/to/skills/agy \
  --model <the-claude-model-id-powering-your-session> \
  --max-iterations 5 --verbose
```

Apply the resulting `best_description` to `SKILL.md` only if it beats the current
one on the held-out set.

---

## When you update the skill — the checklist

1. **Make your edits** to `SKILL.md` / `references/flags.md`.
2. **Run the lint** — `python3 evals/lint_agy_commands.py`. Green before commit.
3. **If you bumped the supported agy version** (or the lint flags drift):
   re-capture and update `references/flags.md` —
   ```bash
   agy --version
   agy --help
   agy models
   ```
   update the version stamp, fix changed flags/subcommands/models, re-run the
   lint. If you added a new value-taking flag or subcommand, update `VALUE_FLAGS`
   / `SUBCOMMANDS` in `lint_agy_commands.py`.
4. **If you changed `description:`** (the trigger), run eval 2 and confirm the
   held-out score didn't regress.

### Capability smoke tests (manual, opt-in — metered/online/slow, so run when needed)

Behaviors the lint can't see. After an agy upgrade, if the skill relies on them,
confirm once (mind the ~2–3 min cold start):

- **Topic-conversation capture + resume (the cache-file mechanism):**
  ```bash
  agy -p "remember the number 42"
  # read the id for this dir, then resume by it:
  python3 -c "import json,os;p=os.path.expanduser('~/.gemini/antigravity-cli/cache/last_conversations.json');m=json.load(open(p)) if os.path.exists(p) else {};print(m.get(os.getcwd()) or m.get(os.path.realpath(os.getcwd())) or '')"
  agy --conversation <that-uuid> -p "what number did I ask you to remember?"
  ```
  The last call should recall "42" — confirms the `last_conversations.json` →
  UUID capture and `--conversation <id>` resume still work.
- **Empty-stdout guard ([#76](https://github.com/google-antigravity/antigravity-cli/issues/76)):**
  ```bash
  agy -p "reply with exactly: pong" | cat   # should print "pong", not empty
  ```
  If piped output is empty on exit 0, the bug is live on this build — the skill's
  retry-once guard is load-bearing.

---

## Notes specific to agy (vs codex / gemini)

- **No read-only mode.** Unlike codex (`--sandbox read-only`) and gemini
  (`plan`), `agy -p` auto-runs tools and **acts by default**. The skill enforces
  read-only intent via the *prompt*, not a flag — untestable by the lint, so it's
  a body-of-the-skill concern.
- **Multi-model, by trigger word.** agy runs Gemini / Claude / GPT-OSS; the skill
  maps the named tool to a model (gemini→Gemini, "with Claude Opus"→Claude). A
  bad model string is silently ignored, so the model table in `references/flags.md`
  is the source of truth, kept in sync with `agy models`.
- **Id capture is post-call.** No `--session-id` (gemini) and no printed id
  (codex) — the UUID is read from `~/.gemini/antigravity-cli/cache/last_conversations.json`
  after the call. Behavioral; covered by the smoke test, not the lint.
- **Cold start + #76 stdout** are the two operational hazards (generous timeout;
  empty-output retry). Neither is a flag, so neither is lint-visible.

A future cleanup could merge the codex/gemini/agy lints into one parameterized
lint (CLI name + subcommand/value-flag sets + help layout); for now they're
sibling copies that share the help-parser logic.
