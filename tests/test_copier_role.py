"""Focused static checks for the Copier role."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = (ROOT / "roles/copier/defaults/main.yml").read_text(encoding="utf-8")
TASKS = (ROOT / "roles/copier/tasks/main.yml").read_text(encoding="utf-8")
DOCS = (ROOT / "docs/copier.qmd").read_text(encoding="utf-8")


class CopierRoleTests(unittest.TestCase):
    def test_installs_the_template_extension_with_copier(self):
        self.assertIn("copier_package: copier", DEFAULTS)
        self.assertIn(
            "copier_template_extensions_package: copier-template-extensions",
            DEFAULTS,
        )
        self.assertIn("- --with", TASKS)
        self.assertIn("{{ copier_template_extensions_package }}", TASKS)

    def test_manages_copier_in_the_target_users_uv_environment(self):
        self.assertIn('become_user: "{{ target_user }}"', TASKS)
        self.assertIn('HOME: "{{ target_home }}"', TASKS)
        self.assertIn('UV_TOOL_DIR: "{{ copier_uv_tool_dir }}"', TASKS)
        self.assertIn('UV_TOOL_BIN_DIR: "{{ copier_uv_tool_bin_dir }}"', TASKS)
        self.assertIn('PATH: "{{ copier_uv_tool_bin_dir }}:', TASKS)
        self.assertRegex(TASKS, r"- uv\n\s+- tool\n\s+- list")

    def test_repairs_an_existing_uv_tool_missing_the_extension(self):
        self.assertIn("- --force", TASKS)
        self.assertIn(
            "copier_template_extensions_package not in copier_uv_tools.stdout",
            TASKS,
        )
        self.assertIn("changed_when: false", TASKS)

    def test_docs_explain_the_extension_and_trust_requirement(self):
        self.assertIn("copier_template_extensions.TemplateExtensionLoader", DOCS)
        self.assertIn("--trust", DOCS)
        self.assertIn("does not install Python dependencies", DOCS)
        self.assertIn("--tags baseline,copier", DOCS)


if __name__ == "__main__":
    unittest.main()
