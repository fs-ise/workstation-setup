"""Focused static checks for the LaTeX role and its integration."""

import unittest
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "roles/latex/defaults/main.yml"
TASKS_PATH = ROOT / "roles/latex/tasks/main.yml"
BASELINE_DEFAULTS_PATH = ROOT / "roles/baseline/defaults/main.yml"
BASELINE_TASKS_PATH = ROOT / "roles/baseline/tasks/main.yml"
PLAYBOOK_PATH = ROOT / "playbooks/lab-stack.yml"
AUDIT_PATH = ROOT / "group_vars/all/package_audit.yml"
YAML_PARSER = YAML(typ="safe")

LATEX_PACKAGES = {
    "texlive-scheme-full",
    "texlive-lang-german",
    "texlive-latex-extra",
    "texlive-xetex",
    "texstudio",
    "untex",
}


class LatexRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defaults = YAML_PARSER.load(DEFAULTS_PATH)
        cls.tasks = YAML_PARSER.load(TASKS_PATH)
        cls.baseline_defaults = YAML_PARSER.load(BASELINE_DEFAULTS_PATH)
        cls.playbook = YAML_PARSER.load(PLAYBOOK_PATH)
        cls.audit = YAML_PARSER.load(AUDIT_PATH)

    def test_role_files_exist(self):
        self.assertTrue(DEFAULTS_PATH.is_file())
        self.assertTrue(TASKS_PATH.is_file())

    def test_defaults_declare_expected_packages(self):
        self.assertIs(self.defaults["latex_install_texlive_scheme_full"], True)
        self.assertEqual(
            self.defaults["latex_texlive_packages"],
            ["texlive-lang-german", "texlive-latex-extra", "texlive-xetex"],
        )
        self.assertEqual(self.defaults["latex_additional_packages"], ["texstudio", "untex"])

    def test_install_conditions_are_mutually_exclusive_and_empty_safe(self):
        tasks = {task["name"]: task for task in self.tasks}
        full_when = tasks["Install the full TeX Live scheme"]["when"]
        selected_when = tasks["Install the selected TeX Live packages"]["when"]
        additional_when = tasks["Install additional LaTeX packages"]["when"]
        self.assertEqual(full_when, "latex_install_texlive_scheme_full | bool")
        self.assertIn("not (latex_install_texlive_scheme_full | bool)", selected_when)
        self.assertIn("latex_texlive_packages | length > 0", selected_when)
        self.assertEqual(additional_when, "latex_additional_packages | length > 0")

    def test_role_does_not_hide_installation_failures(self):
        self.assertNotIn("failed_when", TASKS_PATH.read_text(encoding="utf-8"))

    def test_baseline_has_no_latex_ownership(self):
        baseline_text = (
            BASELINE_DEFAULTS_PATH.read_text(encoding="utf-8")
            + BASELINE_TASKS_PATH.read_text(encoding="utf-8")
        ).lower()
        removed_variable = "baseline_install_" + "texlive_scheme"
        for value in LATEX_PACKAGES | {removed_variable, "latex"}:
            self.assertNotIn(value, baseline_text)

    def test_latex_precedes_quarto_and_has_only_latex_tag(self):
        roles = self.playbook[0]["roles"]
        role_names = [role["role"] for role in roles]
        latex = roles[role_names.index("latex")]
        self.assertLess(role_names.index("latex"), role_names.index("quarto"))
        self.assertEqual(latex["tags"], ["latex"])

    def test_package_audit_assigns_packages_to_latex(self):
        managed = self.audit["package_audit_managed_packages"]
        self.assertTrue(LATEX_PACKAGES.issubset(managed))
        audit_text = AUDIT_PATH.read_text(encoding="utf-8")
        latex_section = audit_text.split("# roles/latex", 1)[1].split("# roles/keepassxc", 1)[0]
        for package in LATEX_PACKAGES:
            self.assertIn(f"  - {package}\n", latex_section)


if __name__ == "__main__":
    unittest.main()
