"""Focused static checks for the Okular role and playbook wiring."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = (ROOT / "roles/okular/defaults/main.yml").read_text(encoding="utf-8")
TASKS = (ROOT / "roles/okular/tasks/main.yml").read_text(encoding="utf-8")
PLAYBOOK = (ROOT / "playbooks/lab-stack.yml").read_text(encoding="utf-8")
AUDIT_POLICY = (ROOT / "group_vars/all/package_audit.yml").read_text(encoding="utf-8")


class OkularRoleTests(unittest.TestCase):
    def test_role_installs_and_owns_okular_package(self):
        self.assertIn("okular_packages:\n  - okular", DEFAULTS)
        self.assertIn("okular_managed_dnf_packages: \"{{ okular_packages }}\"", DEFAULTS)
        self.assertIn("ansible.builtin.dnf:", TASKS)
        self.assertIn('name: "{{ okular_packages }}"', TASKS)
        self.assertIn("state: present", TASKS)

    def test_normal_playbook_exposes_okular_tag(self):
        self.assertIn("- role: okular\n      tags: [okular]", PLAYBOOK)

    def test_okular_is_not_a_package_audit_exception(self):
        self.assertNotIn("  - okular\n", AUDIT_POLICY)


if __name__ == "__main__":
    unittest.main()
