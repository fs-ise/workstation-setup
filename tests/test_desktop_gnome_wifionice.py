"""Adapter-independent checks for the WIFIonICE NetworkManager tasks."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "roles/desktop_gnome/defaults/main.yml"
TASKS_PATH = ROOT / "roles/desktop_gnome/tasks/main.yml"


class DesktopGnomeWifioniceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defaults = DEFAULTS_PATH.read_text(encoding="utf-8")
        cls.tasks = TASKS_PATH.read_text(encoding="utf-8")
        read_start = cls.tasks.index("- name: Read WIFIonICE cloned MAC address setting")
        modify_start = cls.tasks.index(
            "- name: Configure WIFIonICE to use the permanent MAC address"
        )
        next_task = cls.tasks.index("- name: Install Dropbox", modify_start)
        cls.read_task = cls.tasks[read_start:modify_start]
        cls.modify_task = cls.tasks[modify_start:next_task]

    def test_feature_is_enabled_by_default(self):
        self.assertIn(
            "desktop_gnome_configure_wifionice_permanent_mac: true", self.defaults
        )

    def test_read_is_safe_and_does_not_report_changes(self):
        expected_argv = """      - nmcli
      - --get-values
      - 802-11-wireless.cloned-mac-address
      - connection
      - show
      - WIFIonICE"""
        self.assertIn(expected_argv, self.read_task)
        self.assertIn("  changed_when: false", self.read_task)
        self.assertIn("  failed_when: false", self.read_task)
        self.assertIn(
            "when: desktop_gnome_configure_wifionice_permanent_mac | bool",
            self.read_task,
        )

    def test_modify_requires_existing_non_permanent_profile(self):
        expected_argv = """      - nmcli
      - connection
      - modify
      - WIFIonICE
      - 802-11-wireless.cloned-mac-address
      - permanent"""
        self.assertIn(expected_argv, self.modify_task)
        self.assertIn("desktop_gnome_wifionice_cloned_mac.rc == 0", self.modify_task)
        self.assertIn(
            'desktop_gnome_wifionice_cloned_mac.stdout | trim != "permanent"',
            self.modify_task,
        )
        self.assertNotIn("changed_when: false", self.modify_task)
        self.assertNotIn("connection up", self.modify_task)
        self.assertNotIn("connection down", self.modify_task)


if __name__ == "__main__":
    unittest.main()
