"""Container-safe checks for the Copilot-key evsieve installation."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "roles/keyboard_copilot_rightctrl/defaults/main.yml"
TASKS_PATH = ROOT / "roles/keyboard_copilot_rightctrl/tasks/main.yml"


class KeyboardCopilotRightCtrlRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defaults = DEFAULTS_PATH.read_text(encoding="utf-8")
        cls.tasks = TASKS_PATH.read_text(encoding="utf-8")
        cls.role = cls.defaults + cls.tasks

    def test_obsolete_release_asset_is_not_used(self):
        self.assertNotIn("keyboard_copilot_rightctrl_evsieve_artifacts", self.role)
        self.assertNotIn("releases/download", self.role)
        self.assertNotIn("ansible.builtin.get_url", self.tasks)

    def test_source_is_pinned_to_exact_commit(self):
        self.assertIn("162839865e85c65cfc6d4591218e1320378bf079", self.defaults)
        self.assertIn('version: "{{ keyboard_copilot_rightctrl_evsieve_commit }}"', self.tasks)

    def test_build_dependencies_are_declared(self):
        for package in ("cargo", "evtest", "libevdev", "libevdev-devel"):
            self.assertIn(f"  - {package}\n", self.defaults)
        self.assertIn(
            'name: "{{ keyboard_copilot_rightctrl_managed_dnf_packages }}"',
            self.tasks,
        )

    def test_build_condition_tracks_source_and_binary(self):
        self.assertIn("keyboard_copilot_rightctrl_evsieve_checkout.changed or", self.tasks)
        self.assertIn(
            "not keyboard_copilot_rightctrl_evsieve_compiled_stat.stat.exists",
            self.tasks,
        )

    def test_build_and_install_are_content_idempotent(self):
        self.assertNotIn("creates:", self.tasks)
        self.assertIn("ansible.builtin.copy:", self.tasks)
        self.assertIn("        remote_src: true", self.tasks)
        self.assertNotIn("        force: true", self.tasks)


if __name__ == "__main__":
    unittest.main()
