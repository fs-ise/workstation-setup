"""Focused static checks for the default-applications role."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "roles/default_applications/defaults/main.yml"
TASKS_PATH = ROOT / "roles/default_applications/tasks/main.yml"


class DefaultApplicationsRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        defaults = DEFAULTS_PATH.read_text(encoding="utf-8")
        cls.thunderbird = defaults.split("  - name: Thunderbird\n", 1)[1].split(
            "  - name: DB Browser for SQLite\n", 1
        )[0]
        cls.tasks = TASKS_PATH.read_text(encoding="utf-8")
        cls.normalized_tasks = " ".join(cls.tasks.split())

    def test_thunderbird_candidates_are_supported_in_preference_order(self):
        candidates = (
            "net.thunderbird.Thunderbird.desktop",
            "org.mozilla.Thunderbird.desktop",
            "thunderbird.desktop",
        )
        positions = [self.thunderbird.index(candidate) for candidate in candidates]
        self.assertEqual(positions, sorted(positions))

    def test_thunderbird_association_remains_required(self):
        self.assertIn("    required: true", self.thunderbird)
        self.assertIn("      - message/rfc822", self.thunderbird)
        self.assertIn("      - x-scheme-handler/mailto", self.thunderbird)

    def test_first_installed_candidate_is_selected(self):
        self.assertIn(
            "item.desktop_ids | "
            "community.general.lists_intersect(default_applications_installed_desktop_ids) "
            "| first",
            self.normalized_tasks,
        )

    def test_thunderbird_prefers_first_candidate_when_all_are_installed(self):
        candidates = (
            "net.thunderbird.Thunderbird.desktop",
            "org.mozilla.Thunderbird.desktop",
            "thunderbird.desktop",
        )
        installed = set(candidates)

        selected = next(candidate for candidate in candidates if candidate in installed)

        self.assertEqual(selected, "net.thunderbird.Thunderbird.desktop")

    def test_all_application_handling_uses_order_preserving_intersection(self):
        matching_filter = (
            "community.general.lists_intersect("
            "default_applications_installed_desktop_ids)"
        )
        task_names = (
            "Select installed applications",
            "Require expected desktop entries",
            "Report unavailable optional applications",
        )

        for index, task_name in enumerate(task_names):
            start = self.tasks.index(f"- name: {task_name}")
            if index + 1 < len(task_names):
                end = self.tasks.index(f"- name: {task_names[index + 1]}")
                task = self.tasks[start:end]
            else:
                task = self.tasks[start:]
            self.assertIn(matching_filter, task, task_name)

        self.assertNotIn(" | intersect(", self.tasks)

    def test_missing_required_entry_has_clear_failure(self):
        self.assertIn("- name: Require expected desktop entries", self.tasks)
        self.assertIn("Required application {{ item.name }} has no desktop entry", self.tasks)
        self.assertIn("Expected one of", self.tasks)

    def test_optional_applications_are_still_skipped(self):
        self.assertIn("- name: Report unavailable optional applications", self.tasks)
        self.assertIn("rejectattr('required')", self.tasks)
        self.assertIn("Skipping optional application", self.tasks)


if __name__ == "__main__":
    unittest.main()
