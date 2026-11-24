# New-session bootstrap and short prompts

Use these prompts with any repository-aware assistant, including ChatGPT, Codex or Claude Code. Replace the project URL, and optionally specify an issue, PR, branch or handover. The target project and the skill repository are distinct. All permissions are supplied by the host; this skill does not establish connections itself.

## New chat — recover project context (read-only)

Copy the following, changing the project repository URL. Pin the skill URL to an approved commit or tag for reproducibility; the example uses the proposed normal post-merge path on main. For branch review use the branch URL instead.

> We develop this software project using GitHub as the shared source of truth between independent remote and local coding agents.
>
> Project repository: <PROJECT_REPOSITORY_URL>
>
> Read the Agent Handover skill at https://github.com/sparklingneuronics/sparkling-skills/blob/main/plugins/collaboration/skills/agent-handover/SKILL.md and its referenced handover template. Use available repository tools to inspect the project, not the skills repository as the project. Follow the project's AGENTS.md, CLAUDE.md if present, README and available architecture, vision, roadmap and status documents.
>
> Inspect the current default branch and commit, relevant open issues and pull requests, and latest applicable handover linked from those issues or stored in HANDOVER.md or docs/handovers/. Treat local unpushed work as unknown. Do not rely on previous chats.
>
> Report current status, active work and ownership, verified versus reported test results, limitations, what can be done in this environment, what needs another environment, and the recommended next bounded task. Do not change files or start implementation until I authorize work. If access is unavailable, say what you cannot inspect and request only the missing reference or access.
>
> When authorized, work on an isolated branch, preserve existing work, follow project policy, and use the shared handover format with exact code and handover commits, test results, evidence and remaining tasks. Do not assume permission to merge, deploy or publish.

## Receive a bounded task

> Use the agent-handover skill. Project: <PROJECT_REPOSITORY_URL>. Review <ISSUE_OR_PR_OR_HANDOVER_LINK> and its exact implementation commit. Protect existing work, confirm your scope, perform the requested implementation or verification, and report results. Commit and push the scoped work if authorized; prepare the next handover if needed.

## Stop and hand over

> Use the agent-handover skill. Reach a safe checkpoint without starting new features. Preserve unfinished work, run relevant available tests, and record the handover in the project repository. Commit and push the scoped checkpoint if authorized. Return branch, implementation SHA, handover SHA, issue/PR, evidence and blockers. Stop after the checkpoint.

## Review a returned handover

> Use the agent-handover skill. Review <HANDOVER_OR_PR_LINK> against the agreed acceptance criteria and exact tested commit. Check the actual diff and evidence. Identify remaining risks and recommend acceptance or fixes. Do not merge without approval.

## Project adoption

Add a short pointer in the consuming project's AGENTS.md and/or CLAUDE.md (adapt to its existing conventions):

> For cross-agent collaboration, checkpoints or new-session recovery, follow the agent-handover skill from sparkling-skills. Use the shared template and link handover records from relevant issues/PRs. Project-specific policies remain authoritative. Keep test evidence tied to the exact implementation commit.

Keep handovers in the consuming project, not in this shared skills repository. Install the entire skill folder with references for local agents, or use an accessible pinned URL for remote chat. See [the plugin README](../../../README.md) for installation and validation.
