---
name: agent-handover
description: Coordinate development across independent coding agents, local or remote. Use when explicitly asked to hand over work, checkpoint for another agent, resume a project in a new chat, receive a handover, or coordinate local and remote development. Do not invoke another agent or CLI merely because it is named in a handover.
---

# Agent collaboration and handover

## Principles
This is a durable handover protocol, not live delegation. It does not start another agent, schedule work, or automatically grant GitHub access. The user or an explicitly authorized integration initiates the next session. Use a read-only posture for context recovery and review unless changes are authorized. The existing dispatch plugin is independent and is not required.

Git is the shared source of truth, not conversation history. Use the project's own instructions for architecture, priorities, security and release policies. This skill is independent of language, framework, agent vendor and hardware. Assign work by verified capabilities, not by agent name. A remote agent may implement and test portable code; a local agent may do environment-specific execution, private integrations, hardware validation, or any other work it is best equipped for. Neither agent assumes access to the other's working tree or session.

## Receive or resume
1. Establish repository identity, actual available permissions/tools, default branch and current task. Read AGENTS.md (and CLAUDE.md if applicable), README and any available vision, architecture, roadmap and status documents. Read relevant issues, PRs and the latest applicable handover. Use the current commit and branch, not a remembered version. For local checkout, inspect git status and fetch remote refs without modifying the working tree; for remote-only tools inspect branch/PR metadata and files at explicit refs.
2. Confirm the source and destination branches, exact code commit, handover status, acceptance criteria, scope and file ownership. Search for in-flight branches and issues. If a relevant handover is not visible, report that fact instead of assuming the local work is complete.
3. Acknowledge receipt in the issue/PR when authorized: code SHA, task, planned scope, validation capability and any blockers. If the same files are being edited elsewhere, coordinate or wait for a checkpoint; do not overwrite.
4. If the user only asks to restore context, report a brief state summary and next recommended action without initiating new implementation. If the user authorizes implementation, proceed within scope.

## Implement
- Use a dedicated feature branch/worktree when practical; do not modify another agent's working branch without agreement. Keep changes narrow and reversible. Preserve user changes, existing behavior and project conventions.
- Record issue ownership and scope in the issue or PR. Do not claim that informal issue comments are exclusive locks; resolve concurrent ownership before overlapping edits.
- Inspect real code and run the tests available in the actual environment. Separate implemented, passed, failed, not run, and blocked. State environment, command, result and evidence. Never claim a hardware-dependent or private integration test has been performed remotely unless it actually has.
- For unavailable verification, provide exact commands and expected observable results for the receiving agent. Keep any security-sensitive artifacts, credentials, private data and machine-specific paths out of published records. Use approved storage for large files.
- Do not merge, publish, deploy, force-push, reset, stash someone else's work or change access controls without authorization. Follow repo policies and actual permissions.

## Send a handover
When asked to hand over or stop, finish only a safe logical checkpoint; do not start additional features. Preserve unfinished work. Check the diff/status and run relevant available tests. Commit scoped work on the agreed branch and push when authorized; report anything not pushed. Never stage unrelated user changes.

Use [the handover template](references/HANDOVER-TEMPLATE.md). Store the record in a stable project location, preferably docs/handovers/<issue-or-task>-<date>-<short-code-sha>.md; a root HANDOVER.md is acceptable if the project already uses it. Keep historical records; use the issue/PR to link the newest applicable handover. Update project status if appropriate without overwriting newer progress.

Record the exact implementation commit SHA (before the handover-document commit), then commit the record separately if necessary. Verify the remote branch/ref after push; report both implementation SHA and final handover commit SHA in the PR/comment and user summary. Do not attempt to embed a commit's own SHA in that same commit.

If a handover cannot be pushed or tests are blocked, mark it incomplete/blocked and state the action required. Do not say the receiving agent has started. Stop after the requested checkpoint and wait for explicit continuation.

## Receive verification results
Review changes against the agreed baseline and acceptance criteria. Match evidence to code SHA. If validation requires fixes, keep the issue open and record exact remaining work. If all criteria pass, propose acceptance/merge under the repo's policy. A handover is not a merge approval.

## Minimal handover message
Return repository, branch, exact implementation SHA, final handover SHA, issue/PR, record path, status, validation still needed, and one next instruction. The receiving agent should be able to continue with those references alone.
