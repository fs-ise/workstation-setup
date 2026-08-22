"""Focused ownership checks for the Obsidian role."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ObsidianRoleTests(unittest.TestCase):
    def test_role_owns_flatpak_installation(self):
        defaults = (ROOT / "roles/obsidian/defaults/main.yml").read_text()
        tasks = (ROOT / "roles/obsidian/tasks/main.yml").read_text()

        self.assertIn("obsidian_flatpak_id: md.obsidian.Obsidian", defaults)
        self.assertIn("obsidian_managed_flatpak_packages:", defaults)
        self.assertIn("community.general.flatpak:", tasks)
        self.assertIn('name: "{{ obsidian_managed_flatpak_packages }}"', tasks)

    def test_desktop_gnome_no_longer_owns_obsidian(self):
        desktop_role = "".join(
            path.read_text()
            for path in (ROOT / "roles/desktop_gnome").rglob("*")
            if path.is_file()
        ).lower()
        self.assertNotIn("obsidian", desktop_role)

    def test_lab_stack_includes_role_by_default(self):
        playbook = (ROOT / "playbooks/lab-stack.yml").read_text()
        self.assertEqual(playbook.count("- role: obsidian"), 1)
        self.assertIn("tags: [obsidian]", playbook)
        self.assertNotIn("never, obsidian", playbook)


if __name__ == "__main__":
    unittest.main()
