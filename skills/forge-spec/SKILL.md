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
6. Present the full spec and its path, then ask: “Approve this spec, or request changes?” Wait for the user's explicit choice. Do not treat silence, general praise, or unrelated instructions as approval. If the user requests changes, revise the spec and show the complete revised document before asking again. If the user approves, persist that approval as described below.

## Approve a specification

When asked to approve a workflow, require its ID and display the complete current spec. Ask the user to choose in chat: approve it or request changes. Do not require a terminal command or digest from the user.

After the user explicitly approves, run the bundled helper from the target repository root. First get the current digest, then persist approval against that exact digest:

```sh
python3 "<absolute skill directory>/scripts/forge_state.py" spec-hash "<workflow-id>"
python3 "<absolute skill directory>/scripts/forge_state.py" record-chat-approval "<workflow-id>" "<digest returned above>"
```

Resolve the helper from this skill's absolute `SKILL.md` path. Never ask the user to copy or type the digest. The helper refuses to record approval if the spec changes between the digest check and the write. Confirm the write succeeded before saying approval was recorded.

Older workflows can use the same chat approval flow; the bundled helper reads their existing state and records the current spec digest after explicit approval.

## Approval check

Before any later phase consumes a specification, run the bundled helper from the target repository root:

```sh
./.forge/workflows/<workflow-id>/approve check
```

Proceed only if it reports a valid approval. Missing, malformed, or changed specs must stop the workflow. After revision, show the full document again and obtain fresh approval in chat. The state file records the spec digest, so any content change invalidates the old approval.
