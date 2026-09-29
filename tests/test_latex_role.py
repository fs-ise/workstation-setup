"""Focused static checks for the LaTeX role and its integration."""

import unittest
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "roles/latex/defaults/main.yml"
TASKS_PATH = ROOT / "roles/latex/tasks/main.yml"
DISCOVERY_TASKS_PATH = ROOT / "roles/latex/tasks/discover-tinytex.yml"
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
        cls.discovery_tasks = YAML_PARSER.load(DISCOVERY_TASKS_PATH)
        cls.baseline_defaults = YAML_PARSER.load(BASELINE_DEFAULTS_PATH)
        cls.playbook = YAML_PARSER.load(PLAYBOOK_PATH)

    def test_role_files_exist(self):
        self.assertTrue(DEFAULTS_PATH.is_file())
        self.assertTrue(TASKS_PATH.is_file())
        self.assertTrue(DISCOVERY_TASKS_PATH.is_file())

    def test_defaults_declare_expected_packages(self):
        self.assertIs(self.defaults["latex_install_texlive_scheme_full"], False)
        self.assertEqual(self.defaults["latex_additional_packages"], ["texstudio"])
        self.assertEqual(
            self.defaults["latex_tinytex_packages"], ["babel-german", "hanging"]
        )
        self.assertEqual(
            self.defaults["latex_fedora_texlive_packages"],
            ["texlive-babel-german", "texlive-hanging"],
        )

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
        self.assertIn("latex_tinytex_install_required", tinytex_when)
        self.assertEqual(additional_when, "latex_additional_packages | length > 0")
        self.assertIn(
            "latex_fedora_texlive_packages",
            tasks["Install the full TeX Live scheme"]["ansible.builtin.dnf"]["name"],
        )

    def test_tinytex_uses_supported_quarto_cli_and_path_integration(self):
        task = next(
            task for task in self.tasks if task["name"] == "Install TinyTeX through Quarto"
        )
        self.assertEqual(
            task["ansible.builtin.command"]["argv"],
            ["quarto", "install", "tinytex", "--no-prompt", "--update-path"],
        )
        self.assertEqual(task["environment"]["HOME"], "{{ target_home }}")
        self.assertIn("ansible_env.PATH", task["environment"]["PATH"])
        self.assertEqual(task["become_user"], "{{ target_user }}")

    def test_regular_and_symlinked_tlmgr_are_discovered_recursively(self):
        tasks = {task["name"]: task for task in self.discovery_tasks}
        regular = tasks["Find regular TinyTeX package managers"]
        links = tasks["Find symlinked TinyTeX package managers"]
        self.assertEqual(regular["ansible.builtin.find"]["file_type"], "file")
        self.assertEqual(links["ansible.builtin.find"]["file_type"], "link")
        for task in (regular, links):
            find = task["ansible.builtin.find"]
            self.assertEqual(find["paths"], "{{ target_home }}/.TinyTeX/bin")
            self.assertEqual(find["patterns"], "tlmgr")
            self.assertTrue(find["recurse"])
            self.assertEqual(task["become_user"], "{{ target_user }}")
        ci_playbook = (ROOT / "tests/playbooks/ci.yml").read_text(encoding="utf-8")
        self.assertIn(".TinyTeX/bin/x86_64-linux/tlmgr", ci_playbook)

    def test_tinytex_functionality_controls_install_and_rediscovery(self):
        tasks = {task["name"]: task for task in self.tasks}
        discovery = {task["name"]: task for task in self.discovery_tasks}
        probe = discovery["Check TinyTeX package-manager candidates"]
        self.assertEqual(probe["ansible.builtin.command"]["argv"][-1], "--version")
        self.assertFalse(probe["changed_when"])
        self.assertFalse(probe["failed_when"])
        self.assertEqual(probe["become_user"], "{{ target_user }}")
        self.assertIn("ansible_env.PATH", probe["environment"]["PATH"])
        required = tasks["Record whether TinyTeX installation is required"]
        install_required = required["ansible.builtin.set_fact"][
            "latex_tinytex_install_required"
        ]
        self.assertIn("latex_tinytex_working_paths | length == 0", install_required)
        self.assertIn(
            "latex_tinytex_install_required",
            tasks["Rediscover TinyTeX after installation"]["when"],
        )

    def test_incomplete_tinytex_is_preserved_and_errors_are_distinct(self):
        tasks = {task["name"]: task for task in self.tasks}
        link_stat = next(
            task
            for task in self.discovery_tasks
            if task["name"] == "Inspect TinyTeX package-manager symlinks"
        )
        self.assertTrue(link_stat["ansible.builtin.stat"]["follow"])
        failure = tasks["Report a TinyTeX installation failure"]
        message = failure["ansible.builtin.assert"]["fail_msg"]
        self.assertIn("Broken tlmgr symlink", message)
        self.assertIn("No tlmgr executable", message)
        self.assertIn("failed their version check", message)
        self.assertIn("Existing files were not removed", message)

    def test_working_tinytex_skips_reinstallation_on_repeated_runs(self):
        tasks = {task["name"]: task for task in self.tasks}
        install = tasks["Install TinyTeX through Quarto"]
        self.assertIn("latex_tinytex_install_required", install["when"])
        package_check = tasks["Query installed TinyTeX packages"]
        self.assertFalse(package_check["changed_when"])

    def test_old_partial_texlive_packages_are_removed(self):
        role_text = DEFAULTS_PATH.read_text() + TASKS_PATH.read_text()
        for package in ("texlive-lang-german", "texlive-latex-extra", "texlive-xetex"):
            self.assertNotIn(package, role_text)
        ci_playbook = (ROOT / "tests/playbooks/ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("latex_texlive_packages", ci_playbook)

    def test_role_does_not_hide_installation_failures(self):
        tasks_text = TASKS_PATH.read_text(encoding="utf-8")
        self.assertNotIn("ignore_errors", tasks_text)

    def test_tinytex_packages_are_checked_and_installed_as_target_user(self):
        tasks = {task["name"]: task for task in self.tasks}
        check = tasks["Query installed TinyTeX packages"]
        record_missing = tasks[
            "Record missing explicitly managed TinyTeX packages"
        ]
        install = tasks["Install missing explicitly managed TinyTeX packages"]
        self.assertEqual(
            check["ansible.builtin.command"]["argv"],
            [
                "{{ latex_tinytex_bin_dir }}/tlmgr",
                "info",
                "--only-installed",
                "--data",
                "name",
            ],
        )
        self.assertEqual(check["become_user"], "{{ target_user }}")
        self.assertFalse(check["changed_when"])
        self.assertNotIn("failed_when", check)
        missing_expression = record_missing["ansible.builtin.set_fact"][
            "latex_tinytex_missing_packages"
        ]
        self.assertIn("difference", missing_expression)
        self.assertIn("stdout_lines", missing_expression)
        self.assertEqual(install["become_user"], "{{ target_user }}")
        self.assertIn(
            "latex_tinytex_missing_packages | length > 0", install["when"]
        )
        self.assertNotIn("failed_when", install)

    def test_tinytex_package_inventory_regression_cases(self):
        """Missing package queries are data, while tlmgr failures remain fatal."""
        managed = self.defaults["latex_tinytex_packages"]

        def missing(installed):
            return [package for package in managed if package not in installed]

        self.assertEqual(missing([]), ["babel-german", "hanging"])
        self.assertEqual(missing(["babel-german"]), ["hanging"])
        self.assertEqual(missing(["babel-german", "hanging"]), [])

        tasks = {task["name"]: task for task in self.tasks}
        query = tasks["Query installed TinyTeX packages"]
        package_install = tasks["Install missing explicitly managed TinyTeX packages"]
        # Ansible's default command behavior fails on nonzero return codes. Neither
        # inventory errors nor installation errors may be converted to success.
        self.assertNotIn("failed_when", query)
        self.assertNotIn("ignore_errors", query)
        self.assertNotIn("failed_when", package_install)
        self.assertNotIn("ignore_errors", package_install)

    def test_role_verifies_required_files_with_selected_distribution(self):
        tasks = {task["name"]: task for task in self.tasks}
        for name in (
            "Verify required LaTeX files with TinyTeX",
            "Verify required LaTeX files with Fedora TeX Live",
        ):
            self.assertEqual(tasks[name]["loop"], ["german.ldf", "hanging.sty"])
            self.assertEqual(tasks[name]["become_user"], "{{ target_user }}")
            self.assertFalse(tasks[name]["changed_when"])

    def test_fedora_configuration_bypasses_tinytex(self):
        tasks = {task["name"]: task for task in self.tasks}
        self.assertEqual(
            tasks["Install the full TeX Live scheme"]["when"],
            "latex_install_texlive_scheme_full | bool",
        )
        for name in (
            "Discover the Quarto-managed TinyTeX installation",
            "Query installed TinyTeX packages",
            "Verify required LaTeX files with TinyTeX",
        ):
            condition = tasks[name]["when"]
            self.assertIn("not (latex_install_texlive_scheme_full | bool)", condition)

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
        self.assertIn("latex_fedora_texlive_packages", managed)


if __name__ == "__main__":
    unittest.main()
