"""Structural checks for the Thunderbird installation fallback."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = ROOT / "roles/thunderbird/tasks/main.yml"
DEFAULTS_PATH = ROOT / "roles/thunderbird/defaults/main.yml"
TASKS = TASKS_PATH.read_text()
DEFAULTS = DEFAULTS_PATH.read_text()


class ThunderbirdRoleTests(unittest.TestCase):
    def test_dnf_install_uses_block_rescue_flatpak_fallback(self):
        installation = TASKS.split("\n- name: Ensure Thunderbird policies directory exists", 1)[0]

        self.assertIn("- name: Prefer the DNF installation of Thunderbird\n  block:", installation)
        self.assertIn(
            '      ansible.builtin.dnf:\n        name: "{{ thunderbird_managed_dnf_packages }}"',
            installation,
        )
        self.assertIn(
            '  rescue:\n    - name: Install Thunderbird via Flatpak fallback\n'
            '      community.general.flatpak:\n        name: "{{ thunderbird_flatpak_id }}"',
            installation,
        )

    def test_installation_does_not_suppress_failures(self):
        installation = TASKS.split("\n- name: Ensure Thunderbird policies directory exists", 1)[0]

        self.assertNotIn("failed_when", installation)
        self.assertNotIn("is failed", installation)
        self.assertNotIn("  when:", installation)

    def test_package_audit_source_and_flatpak_id_are_preserved(self):
        self.assertIn("thunderbird_managed_dnf_packages:\n  - thunderbird", DEFAULTS)
        self.assertIn("thunderbird_flatpak_id: org.mozilla.Thunderbird", DEFAULTS)


if __name__ == "__main__":
    unittest.main()
