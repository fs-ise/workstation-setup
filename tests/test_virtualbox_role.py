"""Focused checks for VirtualBox conflict-removal behavior."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = ROOT / "roles/virtualbox/tasks/main.yml"


class VirtualBoxRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = TASKS_PATH.read_text(encoding="utf-8")

    def task_block(self, name):
        block = self.tasks.split(f"- name: {name}\n", 1)[1]
        return block.split("\n- name:", 1)[0]

    def test_conflicting_packages_are_removed_without_suppressing_failures(self):
        removal = self.task_block(
            "Remove Oracle VirtualBox packages if present (avoid conflicts)"
        )
        self.assertIn("ansible.builtin.dnf:", removal)
        self.assertIn("VirtualBox-7.2", removal)
        self.assertIn("state: absent", removal)
        self.assertNotIn("failed_when", removal)
        self.assertNotIn("ignore_errors", removal)

    def test_repo_file_is_removed_without_suppressing_failures(self):
        removal = self.task_block("Remove Oracle VirtualBox repo file if present")
        self.assertIn("ansible.builtin.file:", removal)
        self.assertIn("path: /etc/yum.repos.d/virtualbox.repo", removal)
        self.assertIn("state: absent", removal)
        self.assertNotIn("failed_when", removal)
        self.assertNotIn("ignore_errors", removal)


if __name__ == "__main__":
    unittest.main()
