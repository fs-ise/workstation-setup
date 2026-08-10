"""Focused checks for required and optional baseline package semantics."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "roles/baseline/defaults/main.yml"
TASKS_PATH = ROOT / "roles/baseline/tasks/main.yml"
CI_PLAYBOOK_PATH = ROOT / "tests/playbooks/ci.yml"


class BaselineRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defaults = DEFAULTS_PATH.read_text(encoding="utf-8")
        cls.tasks = TASKS_PATH.read_text(encoding="utf-8")
        cls.ci_playbook = CI_PLAYBOOK_PATH.read_text(encoding="utf-8")

    def task_block(self, name):
        block = self.tasks.split(f"- name: {name}\n", 1)[1]
        return block.split("\n- name:", 1)[0]

    def test_core_dependencies_are_required(self):
        required = self.defaults.split("baseline_required_packages:\n", 1)[1]
        required = required.split("\nbaseline_remove_packages_best_effort:", 1)[0]
        for package in ("ca-certificates", "git", "python3"):
            self.assertIn(f"  - {package}\n", required)

    def test_required_install_does_not_suppress_failures(self):
        required = self.task_block("Install required baseline packages")
        self.assertIn('loop: "{{ baseline_required_packages }}"', required)
        self.assertNotIn("failed_when", required)
        self.assertNotIn("ignore_errors", required)

    def test_optional_install_is_best_effort_per_package(self):
        optional = self.task_block("Install optional baseline packages (best effort)")
        self.assertIn('loop: "{{ baseline_optional_packages }}"', optional)
        self.assertIn("failed_when: false", optional)

    def test_ci_uses_current_package_variables(self):
        self.assertIn("    baseline_required_packages: []\n", self.ci_playbook)
        self.assertIn("    baseline_optional_packages: []\n", self.ci_playbook)
        self.assertNotIn("baseline_base_packages", self.ci_playbook)
        self.assertNotIn("baseline_install_packages_best_effort", self.ci_playbook)


if __name__ == "__main__":
    unittest.main()
