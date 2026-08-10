"""Checks for the centralized supported-platform preflight."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = (ROOT / "playbooks/lab-stack.yml").read_text(encoding="utf-8")
TASKS = (ROOT / "roles/preflight/tasks/main.yml").read_text(encoding="utf-8")


class PreflightRoleTests(unittest.TestCase):
    def test_main_playbook_runs_preflight_first(self):
        self.assertLess(PLAYBOOK.index("- role: preflight"), PLAYBOOK.index("- role: baseline"))
        self.assertIn("gather_facts: true", PLAYBOOK)
        self.assertIn("tags: [always, preflight]", PLAYBOOK)

    def test_supported_platform_is_exact(self):
        self.assertIn('ansible_facts["distribution"] == "Fedora"', TASKS)
        self.assertIn('ansible_facts["distribution_major_version"] == "44"', TASKS)
        self.assertIn('ansible_facts["architecture"] == "x86_64"', TASKS)

    def test_failure_reports_detected_and_supported_platforms(self):
        for fact in ("distribution", "distribution_major_version", "architecture"):
            self.assertIn(f'ansible_facts["{fact}"]', TASKS)
        self.assertIn("tested/supported on Fedora 44 x86_64", TASKS)


if __name__ == "__main__":
    unittest.main()
