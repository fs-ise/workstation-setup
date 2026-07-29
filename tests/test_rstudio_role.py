"""Focused static checks for the RStudio role's CRAN installer."""

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


if __name__ == "__main__":
    unittest.main()
