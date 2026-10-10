---
name: forge-plan
description: "Draft and approve a repository-grounded implementation plan from an already approved Forge specification."
---

# Forge planning workflow

Invoke explicitly as `$forge-plan` and provide a workflow ID. Run from the target repository root.

## Create or revise a plan

1. Inspect the target repository's top-level files, applicable `AGENTS.md` instructions, manifests, and components relevant to the approved spec. Do not modify product files.
2. Resolve the bundled helper relative to this skill's absolute `SKILL.md` path: `../forge-spec/scripts/forge_state.py`. Do not use a potentially stale helper copy from a workflow directory.
3. Verify the workflow's current specification approval before using it:

   ```sh
   python3 "<absolute forge-plan skill directory>/../forge-spec/scripts/forge_state.py" check "<workflow-id>"
   ```

   Stop if the workflow ID is missing or invalid, the state or spec is malformed or missing, or the approval is absent or stale. Display the workflow's `spec.md` if the user has not identified which approved workflow to plan; ask for its ID rather than guessing.
4. Read the full approved `spec.md` and get its current digest:

   ```sh
   python3 "<absolute forge-plan skill directory>/../forge-spec/scripts/forge_state.py" spec-hash "<workflow-id>"
   ```

   Ground repository facts in inspected files. Label assumptions and open questions; do not invent files, existing behavior, or validation commands.
5. Write `.forge/workflows/<workflow-id>/plan.md` with YAML front matter containing `source_spec_sha256: <digest from spec-hash>`. Include objective and scope, ordered tasks with stable IDs and concrete outcomes, affected files/components, dependencies and parallelizable tasks, repository-grounded validation, risks, edge cases, assumptions, and unresolved questions.
6. If `plan.md` already exists, show its path and ask whether the user wants a revision. Do not replace it without an explicit revision request. For a requested revision, update the plan and present the complete revised plan before asking for approval again.
7. Present the full plan and its path, then ask: “Approve this plan, or request changes?” Silence, general praise, or unrelated instructions do not count as approval. If changes are requested, revise and show the complete plan again.

## Persist plan approval

Only after the user explicitly approves the displayed plan, persist approval against its current digest with the bundled helper:

```sh
python3 "<absolute forge-plan skill directory>/../forge-spec/scripts/forge_state.py" plan-hash "<workflow-id>"
python3 "<absolute forge-plan skill directory>/../forge-spec/scripts/forge_state.py" record-plan-chat-approval "<workflow-id>" "<digest returned above>"
python3 "<absolute forge-plan skill directory>/../forge-spec/scripts/forge_state.py" plan-check "<workflow-id>"
```

Run commands from the target repository root. Never ask the user to copy or type the digest. The helper checks that the plan's recorded source spec digest still matches the approved spec, verifies the plan digest again while recording, and keeps plan approval separate from spec approval. Confirm `plan-check` succeeds before saying approval was recorded. If any check fails, stop and show the error; do not proceed to implementation.

Before a later workflow stage consumes a plan, it must run `plan-check` with the bundled helper from the target repository root. A changed spec or plan requires review and fresh approval.
