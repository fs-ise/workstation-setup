"""Focused static checks for the Quarto role."""

import re
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

    def test_rpm_download_requires_a_pinned_sha256_checksum(self):
        checksum_match = re.search(
            r'^quarto_rpm_checksum: "(sha256:[0-9a-fA-F]{64})"$',
            DEFAULTS,
            re.MULTILINE,
        )
        self.assertIsNotNone(checksum_match)
        self.assertEqual(
            checksum_match.group(1),
            "sha256:2fe223a4e24d7a85df4ddd64ae124335ed6aa532819ceab322731df6106d337f",
        )
        self.assertIn('checksum: "{{ quarto_rpm_checksum }}"', TASKS)
        self.assertIn("ansible.builtin.assert:", TASKS)
        self.assertIn("^sha256:[0-9a-fA-F]{64}$", TASKS)
        self.assertIn("refusing an unchecked RPM", TASKS)

    def test_checksum_validation_rejects_missing_and_malformed_values(self):
        checksum_pattern = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
        for checksum in ("", "sha256:", "sha256:not-a-digest", "md5:" + "0" * 64):
            self.assertIsNone(checksum_pattern.fullmatch(checksum))

    def test_checksum_is_coupled_to_the_pinned_release(self):
        pinned_release_checksums = {
            "1.10.18": "sha256:2fe223a4e24d7a85df4ddd64ae124335ed6aa532819ceab322731df6106d337f",
        }
        version = re.search(
            r'^quarto_version: "([^"]+)"$', DEFAULTS, re.MULTILINE
        ).group(1)
        checksum = re.search(
            r'^quarto_rpm_checksum: "([^"]+)"$', DEFAULTS, re.MULTILINE
        ).group(1)
        self.assertIn(version, pinned_release_checksums)
        self.assertEqual(checksum, pinned_release_checksums[version])

    def test_unsigned_rpm_exception_is_limited_to_verified_artifact(self):
        self.assertEqual(TASKS.count("disable_gpg_check: true"), 1)
        self.assertLess(TASKS.index('checksum: "{{ quarto_rpm_checksum }}"'),
                        TASKS.index("disable_gpg_check: true"))

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
