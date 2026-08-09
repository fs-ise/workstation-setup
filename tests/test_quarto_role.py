"""Focused static checks for the Quarto role."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "roles/quarto/defaults/main.yml"
TASKS_PATH = ROOT / "roles/quarto/tasks/main.yml"
DEFAULTS = DEFAULTS_PATH.read_text(encoding="utf-8")
TASKS = TASKS_PATH.read_text(encoding="utf-8")


class QuartoRoleTests(unittest.TestCase):
    def test_official_rpm_release_is_pinned(self):
        self.assertIn('quarto_version: "1.10.18"', DEFAULTS)
        self.assertIn('quarto_rpm: "quarto-{{ quarto_version }}-linux-x86_64.rpm"', DEFAULTS)
        self.assertIn("github.com/quarto-dev/quarto-cli/releases/download", DEFAULTS)
        self.assertIn("{{ quarto_rpm }}", DEFAULTS)

    def test_rpm_is_downloaded_and_installed_with_builtin_modules(self):
        self.assertIn("ansible.builtin.get_url:", TASKS)
        self.assertIn("ansible.builtin.dnf:", TASKS)
        self.assertIn('name: "{{ quarto_rpm_path }}"', TASKS)
        self.assertIn("state: present", TASKS)

    def test_tarball_installation_is_removed(self):
        for value in ("quarto_install_dir", "quarto_tarball", "ansible.builtin.unarchive:"):
            self.assertNotIn(value, DEFAULTS + TASKS)

    def test_cleanup_is_limited_to_paths_managed_by_the_legacy_role(self):
        for path in ("/opt/quarto", "/opt/quarto-1.6.42", "/etc/profile.d/quarto.sh"):
            self.assertIn(path, TASKS)
        self.assertNotIn("/usr/local/bin/quarto", TASKS)
        self.assertNotIn("fileglob", TASKS)
        self.assertIn("quarto_legacy_link.stat.islnk", TASKS)


if __name__ == "__main__":
    unittest.main()
