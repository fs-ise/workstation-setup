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
YAML_PARSER = YAML(typ="safe")

LATEX_PACKAGES = {
    "texlive-scheme-full",
    "texlive-lang-german",
    "texlive-latex-extra",
    "texlive-xetex",
    "texstudio",
}


class LatexRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defaults = YAML_PARSER.load(DEFAULTS_PATH)
        cls.tasks = YAML_PARSER.load(TASKS_PATH)
        cls.baseline_defaults = YAML_PARSER.load(BASELINE_DEFAULTS_PATH)
        cls.playbook = YAML_PARSER.load(PLAYBOOK_PATH)

    def test_role_files_exist(self):
        self.assertTrue(DEFAULTS_PATH.is_file())
        self.assertTrue(TASKS_PATH.is_file())

    def test_defaults_declare_expected_packages(self):
        self.assertIs(self.defaults["latex_install_texlive_scheme_full"], False)
        self.assertNotIn("latex_texlive_packages", self.defaults)
        self.assertEqual(self.defaults["latex_additional_packages"], ["texstudio"])

    def test_obsolete_packages_are_not_declared(self):
        obsolete_package = "un" + "tex"
        self.assertNotIn(obsolete_package, self.defaults["latex_additional_packages"])
        self.assertNotIn(obsolete_package, self.defaults["latex_managed_dnf_packages"])

    def test_install_conditions_are_mutually_exclusive_and_empty_safe(self):
        tasks = {task["name"]: task for task in self.tasks}
        full_when = tasks["Install the full TeX Live scheme"]["when"]
        tinytex_when = tasks["Install TinyTeX through Quarto"]["when"]
        additional_when = tasks["Install additional LaTeX packages"]["when"]
        self.assertEqual(full_when, "latex_install_texlive_scheme_full | bool")
        self.assertIn("not (latex_install_texlive_scheme_full | bool)", tinytex_when)
        self.assertIn(
            "not (latex_tinytex_bin.stat.isdir | default(false))", tinytex_when
        )
        self.assertEqual(additional_when, "latex_additional_packages | length > 0")

    def test_tinytex_uses_supported_quarto_cli_and_path_integration(self):
        task = next(
            task for task in self.tasks if task["name"] == "Install TinyTeX through Quarto"
        )
        self.assertEqual(
            task["ansible.builtin.command"]["argv"],
            ["quarto", "install", "tinytex", "--no-prompt", "--update-path"],
        )
        self.assertEqual(task["environment"]["HOME"], "{{ target_home }}")
        self.assertEqual(task["become_user"], "{{ target_user }}")

    def test_old_partial_texlive_packages_are_removed(self):
        role_text = DEFAULTS_PATH.read_text() + TASKS_PATH.read_text()
        for package in ("texlive-lang-german", "texlive-latex-extra", "texlive-xetex"):
            self.assertNotIn(package, role_text)
        ci_playbook = (ROOT / "tests/playbooks/ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("latex_texlive_packages", ci_playbook)

    def test_role_does_not_hide_installation_failures(self):
        tasks_text = TASKS_PATH.read_text(encoding="utf-8")
        self.assertNotIn("failed_when", tasks_text)
        self.assertNotIn("ignore_errors", tasks_text)

    def test_baseline_has_no_latex_ownership(self):
        baseline_text = (
            BASELINE_DEFAULTS_PATH.read_text(encoding="utf-8")
            + BASELINE_TASKS_PATH.read_text(encoding="utf-8")
        ).lower()
        removed_variable = "baseline_install_" + "texlive_scheme"
        for value in LATEX_PACKAGES | {removed_variable, "latex"}:
            self.assertNotIn(value, baseline_text)

    def test_quarto_precedes_latex_and_runs_with_latex_tag(self):
        roles = self.playbook[0]["roles"]
        role_names = [role["role"] for role in roles]
        quarto = roles[role_names.index("quarto")]
        latex = roles[role_names.index("latex")]
        self.assertLess(role_names.index("quarto"), role_names.index("latex"))
        self.assertIn("latex", quarto["tags"])
        self.assertEqual(latex["tags"], ["latex"])

    def test_package_audit_uses_latex_role_declaration(self):
        managed = self.defaults["latex_managed_dnf_packages"]
        self.assertIn("latex_additional_packages", managed)
        self.assertIn("texlive-scheme-full", managed)


if __name__ == "__main__":
    unittest.main()
