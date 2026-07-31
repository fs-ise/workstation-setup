"""Focused static checks for the RStudio role."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "roles/rstudio/defaults/main.yml"
TASKS_PATH = ROOT / "roles/rstudio/tasks/main.yml"


class RStudioRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defaults_text = DEFAULTS_PATH.read_text(encoding="utf-8")
        cls.tasks_text = TASKS_PATH.read_text(encoding="utf-8")

    def default_integer(self, name):
        prefix = f"{name}:"
        line = next(
            line for line in self.defaults_text.splitlines() if line.startswith(prefix)
        )
        return int(line.removeprefix(prefix).strip())

    def task_position(self, task_name):
        marker = f"- name: {task_name}"
        self.assertIn(marker, self.tasks_text)
        return self.tasks_text.index(marker)

    def test_fedora_dependencies_include_libuv_devel(self):
        self.assertIn("  - libuv-devel", self.defaults_text)

    def test_retry_defaults_are_valid(self):
        self.assertGreater(self.default_integer("rstudio_cran_download_timeout"), 0)
        self.assertGreaterEqual(self.default_integer("rstudio_cran_install_attempts"), 1)
        self.assertGreaterEqual(self.default_integer("rstudio_cran_retry_delay"), 0)

    def test_installer_environment_and_dependency_scope(self):
        for variable in (
            "RSTUDIO_CRAN_DOWNLOAD_TIMEOUT",
            "RSTUDIO_CRAN_INSTALL_ATTEMPTS",
            "RSTUDIO_CRAN_RETRY_DELAY",
        ):
            self.assertIn(variable, self.tasks_text)
        self.assertIn(
            'dependencies = c("Depends", "Imports", "LinkingTo")',
            self.tasks_text,
        )
        self.assertNotIn("dependencies = TRUE", self.tasks_text)
        self.assertIn("RSTUDIO_PACKAGES_INSTALLED:", self.tasks_text)

    def test_lock_handling_never_kills_processes(self):
        self.assertIn("pgrep", self.tasks_text)
        self.assertNotIn("pkill", self.tasks_text)
        self.assertNotIn("killall", self.tasks_text)

    def test_container_can_disable_external_installations(self):
        self.assertIn("rstudio_install_desktop: true", self.defaults_text)
        self.assertIn("rstudio_install_cran_packages: true", self.defaults_text)
        self.assertIn("rstudio_install_desktop | bool", self.tasks_text)
        self.assertIn("rstudio_install_cran_packages | bool", self.tasks_text)

    def test_official_posit_signing_key_defaults_are_pinned(self):
        self.assertIn(
            "https://dl.posit.co/public/open/gpg.51C0B5BB19F92D60.key",
            self.defaults_text,
        )
        self.assertIn(
            "8B65E5A107BBEFE3BA99C59751C0B5BB19F92D60",
            self.defaults_text,
        )

    def test_rpm_key_import_verifies_identity_and_transport(self):
        self.assertIn("ansible.builtin.rpm_key:", self.tasks_text)
        self.assertIn('key: "{{ rstudio_rpm_signing_key_url }}"', self.tasks_text)
        self.assertIn("fingerprint:", self.tasks_text)
        self.assertIn(
            '- "{{ rstudio_rpm_signing_key_fingerprint }}"', self.tasks_text
        )
        self.assertIn("validate_certs: true", self.tasks_text)

    def test_rpm_key_is_imported_before_rpm_installation(self):
        key_import = self.task_position("Import the Posit RPM signing key")
        rpm_install = self.task_position("Install the pinned RStudio Desktop RPM")
        self.assertLess(key_import, rpm_install)

    def test_rpm_signature_verification_cannot_be_bypassed(self):
        self.assertIn("disable_gpg_check: false", self.tasks_text)
        for bypass in (
            "disable_gpg_check: true",
            "validate_certs: false",
            "--nogpgcheck",
            "gpgcheck: false",
        ):
            self.assertNotIn(bypass, self.tasks_text)


if __name__ == "__main__":
    unittest.main()
