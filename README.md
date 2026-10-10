# Forge

Forge is a Codex plugin for a reviewable, spec-driven engineering workflow. Version 0.1 provides the specification stage and a persisted approval record.

## Requirements

- Codex CLI or Codex in the ChatGPT desktop app
- Python 3.9 or later

## Skill

Invoke the installed skill explicitly as `$forge-spec` and provide a development task, for example:

```text
$forge-spec Add JWT authentication to the Spring Boot application
```

Codex discovers skills from plugin packages; standalone repo skills use `.agents/skills/<name>/SKILL.md`. Forge uses the plugin package format with `plugin.json`, `skills/forge-spec/SKILL.md`, and a Codex compatibility manifest. See the [Codex skill guide](https://developers.openai.com/codex/skills) and [plugin packaging guide](https://developers.openai.com/plugins/build/plugins).

Forge inspects relevant repository files and creates a draft under `.forge/workflows/<workflow-id>/spec.md`. Review the full document. To approve it, run `./.forge/workflows/<workflow-id>/approve` from the repository root and type `APPROVE`. The helper displays the current digest and stores it automatically, so there is no cache path or digest to copy. Conversational approval alone does not write approval state.

To refresh an existing install after changing the local source, remove the installed copy and add it again, then start a new Codex session. `marketplace upgrade` applies to Git marketplaces, not this local marketplace:

```sh
codex plugin remove forge@forge-local
codex plugin add forge@forge-local
```

## Install from a local marketplace

Codex supports repo-scoped plugin marketplaces. The checked-in `.agents/plugins/marketplace.json` exposes Forge from this repository root for local development. In this repository, add the marketplace and install the plugin:

```sh
codex plugin marketplace add .
codex plugin add forge@forge-local
```

For another repository, copy this plugin folder into that repository's `plugins/forge/` and add this file at `.agents/plugins/marketplace.json`:

```json
{
  "name": "local-repo",
  "plugins": [
    {
      "name": "forge",
      "source": {"source": "local", "path": "./plugins/forge"},
      "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
      "category": "Productivity"
    }
  ]
}
```

Then, from that repository, add and install the plugin:

```sh
codex plugin marketplace add .
codex plugin add forge@local-repo
```

Start a new Codex session and invoke `$forge-spec`. Repo marketplace setup and project-level enablement are covered in the [official plugin packaging guide](https://developers.openai.com/plugins/build/plugins).

Any later workflow stage must verify approval before relying on a spec:

```sh
./.forge/workflows/<workflow-id>/approve check
```

Changing the spec invalidates its approval hash. Review the revision and run the same short approval command again.

## Runtime files

Workflow data lives in the target repository, separate from the installed plugin:

```text
.forge/workflows/<workflow-id>/
├── spec.md
├── state.json
├── approve
└── forge_state.py
```

State is written atomically with mode `0600` where Unix permissions are supported. Forge refuses to replace an existing workflow. Back up `.forge/` with the repository's normal data policy; it contains task descriptions and approval records.

## Approval boundary

Approval requires an interactive terminal and an exact `APPROVE` confirmation after reviewing the artifact. The digest binds the persisted record to the content. This is not an operating-system security boundary: a user or process with write access to `.forge/` can alter its state. Codex's general tool permissions remain in force.

## Validation

Run deterministic tests with:

```sh
python3 -m unittest discover -s tests -v
```

The automated tests do not exercise Codex plugin loading or generated specification quality; those require a manual Codex session.

## Current scope

Forge v0.1 supports natural-language tasks, repository inspection, structured specification drafts, explicit approval, and digest validation. Issue tracker fetch, planning, implementation, worktrees, commit controls, and PR creation are later milestones.
