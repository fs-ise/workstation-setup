"""Focused ownership checks for the borg_vorta role."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLE_DEFAULTS = ROOT / "roles/borg_vorta/defaults/main.yml"
ROLE_TASKS = ROOT / "roles/borg_vorta/tasks/main.yml"
PLAYBOOK = ROOT / "playbooks/lab-stack.yml"


class BorgVortaRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defaults = ROLE_DEFAULTS.read_text()
        cls.tasks = ROLE_TASKS.read_text()
        cls.playbook = PLAYBOOK.read_text()

    def test_role_owns_borg_and_vorta_installation(self):
        self.assertIn("  - borgbackup", self.defaults)
        self.assertIn(
            "borg_vorta_vorta_flatpak_id: com.borgbase.Vorta", self.defaults
        )
        for task_name in (
            "Install BorgBackup",
            "Ensure Flatpak is installed for Vorta",
            "Ensure Flathub is available for Vorta",
            "Install Vorta",
        ):
            self.assertIn(f"- name: {task_name}", self.tasks)

    def test_baseline_and_desktop_do_not_own_borg_or_vorta(self):
        for role_name in ("baseline", "desktop_gnome"):
            role_text = "".join(
                path.read_text()
                for path in (ROOT / "roles" / role_name).rglob("*.yml")
            ).lower()
            self.assertNotIn("borg", role_text)
            self.assertNotIn("vorta", role_text)

    def test_main_playbook_exposes_dedicated_tag(self):
        self.assertEqual(self.playbook.count("- role: borg_vorta"), 1)
        self.assertIn("tags: [borg_vorta, backup, borg, vorta]", self.playbook)


if __name__ == "__main__":
    unittest.main()
