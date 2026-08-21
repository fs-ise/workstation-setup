"""Focused checks for the managed desktop office suite."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OnlyOfficeRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defaults = (ROOT / "roles/onlyoffice/defaults/main.yml").read_text()
        cls.tasks = (ROOT / "roles/onlyoffice/tasks/main.yml").read_text()
        cls.playbook = (ROOT / "playbooks/lab-stack.yml").read_text()
        cls.audit = (ROOT / "group_vars/all/package_audit.yml").read_text()

    def test_onlyoffice_is_installed_idempotently_from_flathub(self):
        self.assertIn("onlyoffice_flatpak_id: org.onlyoffice.desktopeditors", self.defaults)
        self.assertIn("community.general.flatpak:", self.tasks)
        self.assertIn('name: "{{ onlyoffice_flatpak_id }}"', self.tasks)
        self.assertIn("state: present", self.tasks)
        self.assertIn("remote: flathub", self.tasks)
        self.assertNotIn("flatpak_remote", self.tasks)

    def test_role_is_in_normal_stack_with_tag(self):
        self.assertIn("    - role: onlyoffice\n      tags: [onlyoffice]", self.playbook)
        self.assertNotIn("never", self.playbook.split("- role: onlyoffice", 1)[1].split("- role:", 1)[0])

    def test_libreoffice_is_not_exempted_from_package_audit(self):
        self.assertNotIn("^libreoffice-", self.audit)


if __name__ == "__main__":
    unittest.main()
