"""Focused static checks for the RStudio Desktop role."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = (ROOT / "roles/rstudio/defaults/main.yml").read_text(encoding="utf-8")
TASKS = (ROOT / "roles/rstudio/tasks/main.yml").read_text(encoding="utf-8")


class RStudioRoleTests(unittest.TestCase):
    def task_position(self, name):
        marker = f"- name: {name}"
        self.assertIn(marker, TASKS)
        return TASKS.index(marker)

    def test_signing_key_defaults_are_pinned(self):
        self.assertIn("https://dl.posit.co/public/open/gpg.51C0B5BB19F92D60.key", DEFAULTS)
        self.assertIn("8B65E5A107BBEFE3BA99C59751C0B5BB19F92D60", DEFAULTS)

    def test_key_identity_and_certificate_are_verified(self):
        self.assertIn("ansible.builtin.rpm_key:", TASKS)
        self.assertIn("fingerprint:", TASKS)
        self.assertIn("validate_certs: true", TASKS)

    def test_key_import_precedes_rpm_installation(self):
        self.assertLess(self.task_position("Import the Posit RPM signing key"), self.task_position("Install the pinned RStudio Desktop RPM"))

    def test_gpg_verification_cannot_be_bypassed(self):
        self.assertIn("disable_gpg_check: false", TASKS)
        for bypass in ("disable_gpg_check: true", "validate_certs: false", "--nogpgcheck", "gpgcheck: false"):
            self.assertNotIn(bypass, TASKS)

    def test_architecture_validation_is_conditional(self):
        assertion = TASKS[:TASKS.index("- name: Read installed package versions")]
        self.assertIn("when: rstudio_install_desktop | bool", assertion)

    def test_desktop_installation_can_be_disabled(self):
        self.assertIn("rstudio_install_desktop: true", DEFAULTS)
        self.assertGreaterEqual(TASKS.count("rstudio_install_desktop | bool"), 3)

    def test_has_no_cran_or_renviron_management(self):
        for value in ("CRAN", ".Renviron", "R_LIBS_USER", "00LOCK", "R-devel"):
            self.assertNotIn(value, TASKS + DEFAULTS)


if __name__ == "__main__":
    unittest.main()
