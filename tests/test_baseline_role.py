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

    def test_unavailable_fedora_44_packages_are_not_optional(self):
        optional = self.defaults.split("baseline_optional_packages:\n", 1)[1]
        optional = optional.split("\nbaseline_configure_flathub:", 1)[0]
        for package in ("artha", "dict-gcide", "dict-wn", "perl-librdf"):
            self.assertNotIn(f"  - {package}\n", optional)

    def test_obsolete_user_reason_packages_are_removed(self):
        removed = self.defaults.split(
            "baseline_remove_packages_best_effort:\n", 1
        )[1]
        removed = removed.split("\nbaseline_optional_packages:", 1)[0]
        required = self.defaults.split("baseline_required_packages:\n", 1)[1]
        required = required.split("\nbaseline_remove_packages_best_effort:", 1)[0]
        optional = self.defaults.split("baseline_optional_packages:\n", 1)[1]
        optional = optional.split("\nbaseline_configure_flathub:", 1)[0]
        for package in ("gnome-terminal", "libxslt-devel"):
            self.assertIn(f"  - {package}\n", removed)
            self.assertNotIn(f"  - {package}\n", required)
            self.assertNotIn(f"  - {package}\n", optional)

        self.assertIn("  - libxslt\n", optional)

        removal_task = self.task_block("Remove unwanted packages (best effort)")
        self.assertIn('loop: "{{ baseline_remove_packages_best_effort }}"', removal_task)
        self.assertIn("state: absent", removal_task)

    def test_managed_packages_are_derived_from_package_lists(self):
        self.assertIn(
            'baseline_managed_dnf_packages: "{{ baseline_required_packages + baseline_optional_packages }}"',
            self.defaults,
        )

    def test_required_install_does_not_suppress_failures(self):
        required = self.task_block("Install required baseline packages")
        self.assertIn('loop: "{{ baseline_required_packages }}"', required)
        self.assertNotIn("failed_when", required)
        self.assertNotIn("ignore_errors", required)

    def test_optional_install_does_not_suppress_failures(self):
        optional = self.task_block("Install optional baseline packages")
        self.assertIn('loop: "{{ baseline_optional_packages }}"', optional)
        self.assertNotIn("failed_when", optional)
        self.assertNotIn("ignore_errors", optional)

    def test_ci_uses_current_package_variables(self):
        self.assertIn("    baseline_required_packages: []\n", self.ci_playbook)
        self.assertIn("    baseline_optional_packages: []\n", self.ci_playbook)
        self.assertNotIn("baseline_base_packages", self.ci_playbook)
        self.assertNotIn("baseline_install_packages_best_effort", self.ci_playbook)


if __name__ == "__main__":
    unittest.main()
