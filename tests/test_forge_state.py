import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).parents[1] / "skills" / "forge-spec" / "scripts" / "forge_state.py"
SPEC = importlib.util.spec_from_file_location("forge_state", MODULE_PATH)
forge_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(forge_state)
class ForgeStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_cwd = Path.cwd()
        os.chdir(self.temp.name)
        self.workflow_id = "task-123"
        forge_state.init(self.workflow_id, "Add a feature")
        self.directory, self.spec_path, self.state_path = forge_state.workflow_paths(self.workflow_id)
        self.spec_path.write_text("# Specification\n\nInitial text.\n", encoding="utf-8")
        self.approval_command = self.directory / "approve"

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp.cleanup()

    def persist_approval(self):
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        state["approval"] = {"sha256": forge_state.digest(self.spec_path), "approved_at": "now"}
        state["stage"] = "specification_approved"
        self.state_path.write_text(json.dumps(state), encoding="utf-8")

    def test_missing_approval_is_rejected(self):
        with self.assertRaisesRegex(forge_state.ForgeError, "no persisted human approval"):
            forge_state.check(self.workflow_id)

    def test_valid_approval_passes(self):
        self.persist_approval()
        forge_state.check(self.workflow_id)

    def test_changed_spec_invalidates_approval(self):
        self.persist_approval()
        self.spec_path.write_text("# Specification\n\nRevised text.\n", encoding="utf-8")
        with self.assertRaisesRegex(forge_state.ForgeError, "changed after approval"):
            forge_state.check(self.workflow_id)

    def test_malformed_state_is_rejected(self):
        self.state_path.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(forge_state.ForgeError, "malformed"):
            forge_state.check(self.workflow_id)

    def test_init_refuses_existing_workflow(self):
        with self.assertRaisesRegex(forge_state.ForgeError, "already exists"):
            forge_state.init(self.workflow_id, "Overwrite attempt")

    def test_revision_can_be_reapproved(self):
        self.persist_approval()
        self.spec_path.write_text("# Revised specification\n", encoding="utf-8")
        with patch.object(forge_state.sys.stdin, "isatty", return_value=True), \
             patch.object(forge_state.sys.stdout, "isatty", return_value=True), \
             patch("builtins.input", return_value="APPROVE"):
            forge_state.approve(self.workflow_id)
        forge_state.check(self.workflow_id)

    def test_wrong_terminal_confirmation_does_not_approve(self):
        with patch.object(forge_state.sys.stdin, "isatty", return_value=True), \
             patch.object(forge_state.sys.stdout, "isatty", return_value=True), \
             patch("builtins.input", return_value="approved"):
            with self.assertRaisesRegex(forge_state.ForgeError, "did not match"):
                forge_state.approve(self.workflow_id)
        with self.assertRaisesRegex(forge_state.ForgeError, "no persisted human approval"):
            forge_state.check(self.workflow_id)

    def test_init_creates_short_project_local_approval_command(self):
        self.assertTrue(self.approval_command.is_file())
        self.assertTrue(os.access(self.approval_command, os.X_OK))
        self.assertTrue((self.directory / "forge_state.py").is_file())
        self.assertNotIn(str(MODULE_PATH), self.approval_command.read_text(encoding="utf-8"))

    def test_prepare_approval_adds_command_to_existing_workflow(self):
        self.approval_command.unlink()
        (self.directory / "forge_state.py").unlink()
        forge_state.prepare_approval(self.workflow_id)
        self.assertTrue(self.approval_command.is_file())
        self.assertTrue(os.access(self.approval_command, os.X_OK))

    def test_local_command_check_uses_workflow_state(self):
        result = os.spawnv(os.P_WAIT, str(self.approval_command), [str(self.approval_command), "check"])
        self.assertEqual(result, 1)

    def test_symlinked_spec_is_rejected(self):
        original = self.directory / "original.md"
        original.write_text("# spec\n", encoding="utf-8")
        self.spec_path.unlink()
        self.spec_path.symlink_to(original)
        with self.assertRaisesRegex(forge_state.ForgeError, "symlink"):
            forge_state.digest(self.spec_path)


if __name__ == "__main__":
    unittest.main()
