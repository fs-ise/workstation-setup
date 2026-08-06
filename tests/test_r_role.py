"""Focused static checks for the R role."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = (ROOT / "roles/r/defaults/main.yml").read_text(encoding="utf-8")
TASKS = (ROOT / "roles/r/tasks/main.yml").read_text(encoding="utf-8")


class RRoleTests(unittest.TestCase):
    def default_integer(self, name):
        prefix = f"{name}:"
        line = next(line for line in DEFAULTS.splitlines() if line.startswith(prefix))
        return int(line.removeprefix(prefix).strip())

    def test_build_dependencies_include_libuv_devel(self):
        for package in ("R", "R-devel", "gcc", "gcc-c++", "gcc-gfortran", "libuv-devel"):
            self.assertIn(f"  - {package}", DEFAULTS)

    def test_retry_defaults_are_valid(self):
        self.assertGreater(self.default_integer("r_cran_download_timeout"), 0)
        self.assertGreaterEqual(self.default_integer("r_cran_install_attempts"), 1)
        self.assertGreaterEqual(self.default_integer("r_cran_retry_delay"), 0)

    def test_installer_environment_dependency_scope_and_changed_marker(self):
        for variable in ("R_CRAN_REPOSITORY", "R_PACKAGES", "R_CRAN_DOWNLOAD_TIMEOUT", "R_CRAN_INSTALL_ATTEMPTS", "R_CRAN_RETRY_DELAY"):
            self.assertIn(variable, TASKS)
        self.assertIn('dependencies = c("Depends", "Imports", "LinkingTo")', TASKS)
        self.assertNotIn("dependencies = TRUE", TASKS)
        self.assertIn("R_PACKAGES_INSTALLED:", TASKS)
        self.assertIn("changed_when:", TASKS)

    def test_lock_handling_never_kills_processes(self):
        self.assertIn("pgrep", TASKS)
        self.assertNotIn("pkill", TASKS)
        self.assertNotIn("killall", TASKS)

    def test_cran_installation_can_be_disabled(self):
        self.assertIn("r_install_cran_packages: true", DEFAULTS)
        self.assertIn("r_install_cran_packages | bool", TASKS)

    def test_has_no_rstudio_rpm_logic(self):
        for value in ("rpm_key", "get_url", "rstudio_rpm", "Install pinned RStudio"):
            self.assertNotIn(value, TASKS + DEFAULTS)


if __name__ == "__main__":
    unittest.main()
