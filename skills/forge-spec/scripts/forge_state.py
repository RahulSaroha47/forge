#!/usr/bin/env python3
"""Persist and verify human approval for Forge specification artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ROOT = Path(".forge") / "workflows"


class ForgeError(Exception):
    pass


def workflow_paths(workflow_id: str) -> tuple[Path, Path, Path]:
    if not ID_RE.fullmatch(workflow_id):
        raise ForgeError("Workflow ID must contain lowercase letters, digits, and single hyphens.")
    directory = ROOT / workflow_id
    return directory, directory / "spec.md", directory / "state.json"


def reject_symlink(path: Path) -> None:
    for candidate in reversed((path, *path.parents)):
        if candidate == Path("."):
            continue
        if candidate.is_symlink():
            raise ForgeError(f"Refusing to use symlink: {candidate}")


def digest(path: Path) -> str:
    reject_symlink(path)
    if not path.is_file():
        raise ForgeError(f"Specification is missing: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_state(path: Path) -> dict:
    reject_symlink(path)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ForgeError(f"Approval state is missing: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ForgeError(f"Approval state is unreadable or malformed: {path}") from exc
    if not isinstance(state, dict) or state.get("version") != 1:
        raise ForgeError("Approval state has an unsupported or malformed format.")
    if not isinstance(state.get("workflow_id"), str):
        raise ForgeError("Approval state is missing its workflow ID.")
    return state


def atomic_json(path: Path, value: dict) -> None:
    reject_symlink(path)
    temp = path.with_name(path.name + f".tmp-{os.getpid()}")
    reject_symlink(temp)
    try:
        with temp.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.chmod(temp, 0o600)
        os.replace(temp, path)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def install_local_approval(directory: Path) -> None:
    reject_symlink(directory)
    helper = directory / "forge_state.py"
    command = directory / "approve"
    reject_symlink(helper)
    reject_symlink(command)
    created = []
    try:
        if not helper.exists():
            with helper.open("xb") as stream:
                stream.write(Path(__file__).read_bytes())
            created.append(helper)
            os.chmod(helper, 0o600)
        if not command.exists():
            wrapper = (
                "#!/bin/sh\n"
                "set -eu\n"
                'command="${1:-approve}"\n'
                'if [ "$#" -gt 0 ]; then shift; fi\n'
                'workflow_id=$(basename "$(dirname "$0")")\n'
                'exec python3 "$(dirname "$0")/forge_state.py" "$command" "$workflow_id" "$@"\n'
            )
            with command.open("x", encoding="utf-8") as stream:
                stream.write(wrapper)
            created.append(command)
            os.chmod(command, 0o700)
    except Exception:
        for path in created:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise


def init(workflow_id: str, task: str) -> None:
    directory, spec, state_path = workflow_paths(workflow_id)
    reject_symlink(Path(".forge"))
    directory.parent.mkdir(parents=True, exist_ok=True)
    reject_symlink(directory.parent)
    try:
        directory.mkdir()
    except FileExistsError as exc:
        raise ForgeError(f"Workflow already exists; refusing to overwrite: {directory}") from exc
    state = {
        "version": 1,
        "workflow_id": workflow_id,
        "task": task,
        "stage": "specification_draft",
        "spec_path": str(spec),
        "approval": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        install_local_approval(directory)
        atomic_json(state_path, state)
    except Exception:
        for path in (state_path, directory / "approve", directory / "forge_state.py"):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        try:
            directory.rmdir()
        except OSError:
            pass
        raise
    print(spec)


def prepare_approval(workflow_id: str) -> None:
    directory, spec, state_path = workflow_paths(workflow_id)
    reject_symlink(directory)
    state = read_state(state_path)
    if state["workflow_id"] != workflow_id or state.get("spec_path") != str(spec):
        raise ForgeError("Approval state does not match this workflow.")
    if not spec.is_file():
        raise ForgeError(f"Specification is missing: {spec}")
    install_local_approval(directory)
    print(directory / "approve")


def record_approval(workflow_id: str, expected_hash: str | None = None) -> str:
    directory, spec, state_path = workflow_paths(workflow_id)
    reject_symlink(directory)
    current_hash = digest(spec)
    if expected_hash is not None and current_hash != expected_hash:
        raise ForgeError("Specification changed during approval; no approval was recorded.")
    state = read_state(state_path)
    if state["workflow_id"] != workflow_id or state.get("spec_path") != str(spec):
        raise ForgeError("Approval state does not match this workflow.")
    state["approval"] = {"sha256": current_hash, "approved_at": datetime.now(timezone.utc).isoformat()}
    state["stage"] = "specification_approved"
    if digest(spec) != current_hash:
        raise ForgeError("Specification changed during approval; no approval was recorded.")
    atomic_json(state_path, state)
    return current_hash


def spec_hash(workflow_id: str) -> str:
    directory, spec, state_path = workflow_paths(workflow_id)
    reject_symlink(directory)
    state = read_state(state_path)
    if state["workflow_id"] != workflow_id or state.get("spec_path") != str(spec):
        raise ForgeError("Approval state does not match this workflow.")
    return digest(spec)


def record_chat_approval(workflow_id: str, expected_hash: str) -> None:
    if not re.fullmatch(r"[a-f0-9]{64}", expected_hash):
        raise ForgeError("Expected specification hash must be a SHA-256 digest.")
    record_approval(workflow_id, expected_hash=expected_hash)
    print(f"Approval recorded for {workflow_id}.")


def approve(workflow_id: str) -> None:
    _, spec, _ = workflow_paths(workflow_id)
    current_hash = digest(spec)
    print(f"Specification: {spec}")
    print(f"SHA-256: {current_hash}")
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ForgeError("Approval requires an interactive terminal; no approval was recorded.")
    answer = input("Type APPROVE to approve this exact specification: ").strip()
    if answer != "APPROVE":
        raise ForgeError("Approval did not match; no approval was recorded.")
    record_approval(workflow_id, expected_hash=current_hash)
    print(f"Approval recorded for {workflow_id}.")


def check(workflow_id: str) -> None:
    directory, spec, state_path = workflow_paths(workflow_id)
    reject_symlink(directory)
    state = read_state(state_path)
    if state["workflow_id"] != workflow_id or state.get("spec_path") != str(spec):
        raise ForgeError("Approval state does not match this workflow.")
    approval = state.get("approval")
    if not isinstance(approval, dict) or not isinstance(approval.get("sha256"), str):
        raise ForgeError("Specification has no persisted human approval.")
    if digest(spec) != approval["sha256"]:
        raise ForgeError("Specification changed after approval; review and approve it again.")
    print(f"Valid approval for {workflow_id} ({approval['sha256']}).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init_parser = sub.add_parser("init", help="create a workflow record without overwriting")
    init_parser.add_argument("workflow_id")
    init_parser.add_argument("task")
    for command in ("approve", "check", "spec-hash"):
        command_parser = sub.add_parser(command)
        command_parser.add_argument("workflow_id")
    record_parser = sub.add_parser(
        "record-chat-approval",
        help="persist approval after explicit approval in the Codex conversation",
    )
    record_parser.add_argument("workflow_id")
    record_parser.add_argument("expected_hash")
    prepare_parser = sub.add_parser("prepare-approval", help="install a short project-local approval command")
    prepare_parser.add_argument("workflow_id")
    args = parser.parse_args()
    try:
        if args.command == "init":
            init(args.workflow_id, args.task)
        elif args.command == "approve":
            approve(args.workflow_id)
        elif args.command == "prepare-approval":
            prepare_approval(args.workflow_id)
        elif args.command == "spec-hash":
            print(spec_hash(args.workflow_id))
        elif args.command == "record-chat-approval":
            record_chat_approval(args.workflow_id, args.expected_hash)
        else:
            check(args.workflow_id)
    except (ForgeError, OSError) as exc:
        print(f"forge: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
