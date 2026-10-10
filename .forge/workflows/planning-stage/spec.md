# Forge planning stage

## Task overview

Add a Forge workflow stage that turns an explicitly approved specification into a reviewable implementation plan. The plan stage should be a separate, explicit workflow invoked after specification approval. This document specifies the feature; it does not implement it.

## Problem statement

Forge v0.1 creates repository-grounded specifications and records approval against the exact spec digest. The repository README lists planning as a later milestone, but there is no workflow for translating an approved spec into ordered engineering work. Users currently have to do that step outside Forge, without a persisted artifact or a clear approval boundary.

## Goals

- Generate a repository-grounded implementation plan from a currently approved Forge specification.
- Save the plan in the existing workflow directory so it can be reviewed and revised.
- Break work into ordered, actionable tasks with dependencies and validation guidance.
- Require explicit user review and approval of the exact plan before a later implementation stage can consume it.
- Preserve existing specification approval records and keep current workflows readable.

## Non-goals

- Fetching issues from an external tracker.
- Editing product source code or implementing the plan.
- Creating worktrees, branches, commits, or pull requests.
- Automatically changing the approved specification to make planning easier.
- Selecting or running an autonomous coding agent for each task.

## Functional requirements

1. Provide an explicit planning workflow, preferably as a separate `$forge-plan` skill, that accepts a workflow ID and runs from the target repository root.
2. Before planning, verify the workflow ID, state file, spec path, and persisted approval. Verify the approval against the current spec digest using the bundled Forge helper. Stop if the approval is missing, malformed, mismatched, or stale.
3. Inspect applicable `AGENTS.md` instructions, repository manifests, and components relevant to the approved spec. The plan must distinguish inspected repository facts from assumptions and must not invent existing files or behavior.
4. Create `.forge/workflows/<workflow-id>/plan.md` containing:
   - a concise objective and scope derived from the approved spec;
   - ordered tasks with stable identifiers, concrete outcomes, and relevant files or components;
   - dependencies between tasks and any parallelizable work;
   - validation commands or checks grounded in repository tooling;
   - risks, edge cases, assumptions, and unresolved questions.
5. Do not modify product files while generating or revising a plan.
6. Do not overwrite an existing plan by default. If a plan already exists, show its path and require an explicit revision request; for revisions, show the full revised plan before seeking approval again.
7. Present the complete plan and ask the user to approve it or request changes. Only an explicit approval records plan approval.
8. Persist plan approval separately from spec approval and bind it to the exact plan digest. Any plan change invalidates that plan approval. Plan approval must not replace or mutate the spec approval.
9. Provide a helper check that later stages can use to verify both that the source spec remains approved and that the current plan has an explicit, digest-valid approval.
10. Keep existing v1 workflow state valid. Any state format change must read existing v1 records without silently granting plan approval.

## Non-functional requirements

- Fail closed on missing or malformed state, invalid workflow IDs, symlinked workflow artifacts, and digest mismatches.
- Write approval state atomically and preserve restrictive file permissions where supported, following the existing approval helper's behavior.
- Keep planning behavior deterministic in its file effects: it may create or revise workflow artifacts only, and it must not edit repository product code.
- Keep instructions usable from the target repository without requiring a globally installed Forge helper; use the bundled helper or the workflow-local copy.

## Acceptance criteria

- Planning refuses to run when the workflow has no recorded spec approval or when the spec has changed since approval.
- A valid approved workflow produces a `plan.md` in that workflow directory with all required planning sections.
- The plan identifies ordered tasks, dependencies, affected repository components, and applicable validation checks.
- Planning does not alter files outside `.forge/workflows/<workflow-id>/`.
- The complete plan is shown before approval is requested; silence or unrelated replies do not count as approval.
- Explicit plan approval records a digest separate from the spec approval, and a subsequent plan edit causes the plan check to fail.
- Existing approved and unapproved v1 workflows continue to pass or fail their existing spec checks as before; neither gains plan approval automatically.
- Tests cover missing/stale spec approval, valid planning, plan overwrite protection, explicit plan approval, changed-plan invalidation, and backward compatibility with v1 state.

## Edge cases

- The user changes the spec after it was approved but before planning begins.
- The spec changes after a plan has been drafted or approved.
- The workflow directory or either artifact is a symlink.
- State or plan files are missing, malformed, or refer to a different workflow ID/path.
- A plan exists without an approval record, or the plan changes between digest calculation and approval persistence.
- The repository has no applicable tests or validation command; the plan must state that rather than fabricate one.
- A task is blocked by an unresolved question; the plan must make the dependency or question visible instead of presenting it as settled.

## Assumptions

- The plan is stored beside the spec in the existing `.forge/workflows/<workflow-id>/` directory.
- Planning is a separate explicit skill so that creating a plan cannot be confused with approving or implementing a specification.
- Plan approval is needed because later implementation is expected to consume a reviewable plan, and approval must be tied to the exact content as it is for specifications.
- The current local approval command can be extended while retaining compatibility with existing v1 workflow state.

## Open questions

- Should the separate planner be named `$forge-plan`, or should planning be a mode of `$forge-spec`?
- Should plan approval use a short local command parallel to `approve`, or should it be chat-only with a helper check reserved for later stages?
- Should a plan revision retain prior approval metadata for audit, or replace it with a new digest and timestamp?

## Relevant existing repository components

- `skills/forge-spec/SKILL.md` defines explicit invocation, repository inspection, no-overwrite behavior, full-artifact review, and chat-based approval.
- `skills/forge-spec/scripts/forge_state.py` creates workflow state, installs a local approval command, hashes specs, records chat or terminal approval, checks approval, and rejects symlinks.
- `tests/test_forge_state.py` covers approval persistence, changed-spec invalidation, workflow overwrite protection, symlink rejection, and local approval commands.
- `README.md` describes Forge v0.1 and names planning as a later milestone after specification approval.
