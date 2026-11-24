# Development handover — <task>

- Repository: <owner/repo or URL>
- Date/time (UTC): <ISO timestamp>
- From / to: <agent or role> / <agent or role>
- Status: ready for review | ready for implementation | ready for local validation | incomplete | blocked
- Issue(s) / PR(s): <links>
- Base branch / base SHA: <ref and exact SHA>
- Work branch / implementation SHA: <ref and exact SHA before this record>
- Remote state: <pushed and verified / not pushed and reason>
- Local-only changes: <none / describe without secrets; include how they are preserved>

## Goal and scope
<Requested outcome, acceptance criteria, exclusions, ownership and areas not to edit.>

## Completed changes
<Files/components, behavior, important design decisions and compatibility impact.>

## Incomplete work and known limitations
<Unfinished implementation, defects, uncertainty, blockers and dependencies.>

## Verification
| Check / command | Environment | Result (pass/fail/not run/blocked) | Evidence / notes |
|---|---|---|---|
| <exact command> | <relevant versions/hardware> | <status> | <path/link and measured result> |

Do not omit failed or unrun required checks. Identify the code SHA tested and any differences from the handover SHA.

## Receiving agent instructions
1. <Safe checkout/fetch steps or explicit GitHub ref; protect existing work.>
2. <Next bounded task and affected files.>
3. <Exact test or reproduction steps, prerequisites and expected observable outcome.>
4. <What to return: changes, evidence and remaining risks.>

## Evidence and artifacts
<Approved links or repo paths; distinguish local-only from accessible artifacts; no secrets or private data.>

## Acceptance and decisions
<Remaining acceptance gates, merge/release permissions, owner decisions required.>

## Handover completion
<After recording and pushing this file, include the final remote handover commit SHA in the issue/PR comment or delivery summary. Do not include a self-referential SHA here.>
