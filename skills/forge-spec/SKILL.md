---
name: forge-spec
description: Create, revise, or verify a repository-grounded Forge specification and its human approval.
---

# Forge specification workflow

Invoke explicitly as `$forge-spec`. Treat the prompt as a task description unless the user clearly asks to revise or approve an existing workflow.

## Create a specification

1. From the target repository root, inspect the project: list top-level files, read applicable `AGENTS.md` instructions and manifests, and inspect components related to the task. Do not modify product code.
2. Ask focused questions if essential requirements are unclear. Otherwise record assumptions and open questions.
3. Choose a concise workflow ID using lowercase letters, digits, and hyphens. Codex lists this skill's absolute `SKILL.md` path with its skill metadata. Resolve the bundled helper relative to that file, at `scripts/forge_state.py`; do not look for it in the target repository. Run `python3 "<absolute skill directory>/scripts/forge_state.py" init "<workflow-id>" "<task description>"` with the target repository as the working directory. This creates `.forge/workflows/<workflow-id>/` and its short local approval command without replacing an existing workflow.
4. Write `spec.md` in that directory. Include task overview, problem statement, goals, non-goals, functional requirements, relevant non-functional requirements, acceptance criteria, edge cases, assumptions, open questions, and relevant existing repository components. Ground repository claims in inspected files.
5. If the workflow or spec already exists, do not overwrite it. Show the existing path and ask for a different workflow ID or an explicit revision request. For a revision, present the proposed changes first, edit the spec, then show the complete revised document.
6. Present the full spec and its path for review. Conversational approval alone does not persist approval.

## Approve a specification

When asked to approve a workflow, require its ID and display the complete current spec. Ask the user to review it. After review, tell them to run the short project-local approval command from the repository root:

```text
./.forge/workflows/<workflow-id>/approve
```

The command displays the current artifact path and digest, then requires the person at the terminal to type `APPROVE`. It records that digest in state. Do not claim approval until the command succeeds or the persisted record passes the check below. Conversational approval alone does not persist approval.

For workflows created by an older Forge version that do not yet have this command, use the bundled helper's `prepare-approval <workflow-id>` operation from the target repository root. This adds the project-local command without changing the spec or existing state. Then give the user the short command above.

## Approval check

Before any later phase consumes a specification, run the bundled helper from the target repository root:

```sh
./.forge/workflows/<workflow-id>/approve check
```

Proceed only if it reports a valid approval. Missing, malformed, or changed specs must stop the workflow. After revision, show the full document again and obtain fresh approval using the project-local command. The state file records the spec digest, so any content change invalidates the old approval.
