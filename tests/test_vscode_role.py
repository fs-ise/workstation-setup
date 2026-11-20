"""Regression checks for VS Code extension provisioning."""

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = ROOT / "roles/vscode/tasks/main.yml"
DEFAULTS_PATH = ROOT / "roles/vscode/defaults/main.yml"


class VSCodeRoleTests(unittest.TestCase):
    def setUp(self):
        self.tasks = yaml.safe_load(TASKS_PATH.read_text(encoding="utf-8"))
        self.defaults = yaml.safe_load(DEFAULTS_PATH.read_text(encoding="utf-8"))

    def test_markdown_and_quarto_extensions_remain_managed(self):
        self.assertIn("yzhang.markdown-all-in-one", self.defaults["vscode_extensions"])
        self.assertIn("quarto.quarto", self.defaults["vscode_extensions"])

    def test_extensions_are_listed_and_installed_with_selected_method(self):
        expected = {
            "rpm": (
                "List installed VS Code extensions from the RPM installation",
                "Install missing VS Code extensions with code CLI",
                "vscode_rpm_extensions",
            ),
            "flatpak": (
                "List installed VS Code extensions from the Flatpak installation",
                "Install missing VS Code extensions for Flatpak",
                "vscode_flatpak_extensions",
            ),
        }
        for _, (list_name, install_name, result_var) in expected.items():
            list_task = next(task for task in self.tasks if task["name"] == list_name)
            install_task = next(
                task for task in self.tasks if task["name"] == install_name
            )
            method = "rpm" if result_var == "vscode_rpm_extensions" else "flatpak"
            self.assertEqual(list_task["register"], result_var)
            self.assertFalse(list_task["changed_when"])
            self.assertEqual(list_task["when"], f"vscode_install_method == '{method}'")
            self.assertTrue(
                any("item not in" in condition for condition in install_task["when"])
            )
            self.assertTrue(
                any(
                    condition == f"vscode_install_method == '{method}'"
                    for condition in install_task["when"]
                )
            )
            self.assertNotIn("changed_when", install_task)
            self.assertNotIn("failed_when", list_task)
            self.assertNotIn("failed_when", install_task)

            for task in (list_task, install_task):
                self.assertEqual(task["become_user"], "{{ target_user }}")
                self.assertEqual(
                    task["environment"]["HOME"], "{{ target_home }}"
                )
                self.assertEqual(
                    task["environment"]["XDG_CONFIG_HOME"],
                    "{{ target_home }}/.config",
                )
                self.assertEqual(
                    task["environment"]["XDG_DATA_HOME"],
                    "{{ target_home }}/.local/share",
                )

        selection = next(
            task for task in self.tasks
            if task["name"] == "Prefer the RPM installation of VS Code"
        )
        rpm_selection = next(
            task for task in selection["block"]
            if task["name"] == "Select the RPM desktop entry"
        )
        flatpak_selection = next(
            task for task in selection["rescue"]
            if task["name"] == "Select the Flatpak desktop entry"
        )
        self.assertEqual(
            rpm_selection["ansible.builtin.set_fact"]["vscode_install_method"],
            "rpm",
        )
        self.assertEqual(
            flatpak_selection["ansible.builtin.set_fact"]["vscode_install_method"],
            "flatpak",
        )

        self.assertTrue(
            all(
                "--force" not in str(task)
                for task in self.tasks
                if "extension" in task["name"].lower()
            )
        )
        self.assertTrue(
            all(
                "|| true" not in str(task)
                for task in self.tasks
                if "extension" in task["name"].lower()
            )
        )


if __name__ == "__main__":
    unittest.main()
