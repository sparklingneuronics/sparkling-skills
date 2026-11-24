# collaboration

A Git-based handover protocol for independent coding agents and repository-aware chats. Unlike dispatch, it does not invoke external CLIs or rely on shared conversation history. It is useful for switching between ChatGPT, Codex, Claude Code or other agents, including work requiring hardware or private local integrations.

## Install / use

After the plugin is reviewed and released on the marketplace's default branch:

```
/plugin marketplace add sparklingneuronics/sparkling-skills
/plugin install collaboration@sparkling-skills
```

In Claude Code, explicitly request the agent-handover skill (or use the skill's namespaced invocation if exposed by your installed version). In Codex, copy the entire `skills/agent-handover/` directory from this plugin into the supported project skill directory (typically `.agents/skills/agent-handover/`) or user skill directory (typically `~/.agents/skills/agent-handover/`); confirm paths with your installed version. Manual Claude Code installation can similarly use the supported `.claude/skills/` directory. Keep the references folder. Do not overwrite an existing customized skill without review. Alternatively instruct any agent to read the skill directly from an accessible repository URL. A repository-aware chat does not automatically install a skill merely because it can read GitHub.

- [Agent handover skill](skills/agent-handover/SKILL.md)
- [Handover template](skills/agent-handover/references/HANDOVER-TEMPLATE.md)
- [New-chat bootstrap and short prompts](skills/agent-handover/references/CHAT-BOOTSTRAP.md)

## Workflow

The user authorizes a bounded task; the sending agent commits scoped changes, records the actual implementation SHA, records available test results, and verifies the pushed handover. The receiving agent reads the issue, PR, handover and source at the specified ref, checks its capabilities and ownership, and performs authorized work. Environment-specific checks are explicitly marked not run or blocked until performed. Project instructions govern merging and release.

## Validation before release

Run the repository's existing release checks and `claude plugin validate .` from the repository root. Validate the standalone plugin with the installed CLI's supported validation command. Exercise the cases in [evals/README.md](skills/agent-handover/evals/README.md). Live CLI discovery and model behavior have not been tested in this proposal; no external CLI is invoked by the skill itself.
