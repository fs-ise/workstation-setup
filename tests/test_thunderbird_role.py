"""Structural checks for the Thunderbird installation fallback."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = ROOT / "roles/thunderbird/tasks/main.yml"
DEFAULTS_PATH = ROOT / "roles/thunderbird/defaults/main.yml"
TASKS = TASKS_PATH.read_text()
DEFAULTS = DEFAULTS_PATH.read_text()


class ThunderbirdRoleTests(unittest.TestCase):
    def test_dnf_install_uses_block_rescue_flatpak_fallback(self):
        installation = TASKS.split("\n- name: Ensure Thunderbird policies directory exists", 1)[0]

        self.assertIn("- name: Prefer the DNF installation of Thunderbird\n  block:", installation)
        self.assertIn(
            '      ansible.builtin.dnf:\n        name: "{{ thunderbird_managed_dnf_packages }}"',
            installation,
        )
        self.assertIn(
            '  rescue:\n    - name: Install Thunderbird via Flatpak fallback\n'
            '      community.general.flatpak:\n        name: "{{ thunderbird_flatpak_id }}"',
            installation,
        )

    def test_installation_does_not_suppress_failures(self):
        installation = TASKS.split("\n- name: Ensure Thunderbird policies directory exists", 1)[0]

        self.assertNotIn("failed_when", installation)
        self.assertNotIn("is failed", installation)
        self.assertNotIn("  when:", installation)

    def test_package_audit_source_and_flatpak_id_are_preserved(self):
        self.assertIn("thunderbird_managed_dnf_packages:\n  - thunderbird", DEFAULTS)
        self.assertIn("thunderbird_flatpak_id: org.mozilla.Thunderbird", DEFAULTS)

    def test_policy_output_is_canonical_and_newline_terminated(self):
        write = TASKS.split("- name: Write Thunderbird enterprise policies", 1)[1]
        self.assertIn("ansible.builtin.copy:", write)
        self.assertIn("to_nice_json(indent=2, sort_keys=true)", write)
        self.assertIn(' }}\\n"', write)
        template = ROOT / "roles/thunderbird/templates/policies.json.j2"
        self.assertFalse(template.exists())

    def test_policy_merge_preserves_existing_extensions_and_policies(self):
        self.assertIn("thunderbird_existing_policies | combine", TASKS)
        self.assertIn(
            "thunderbird_existing_policies.policies.ExtensionSettings | default({})",
            TASKS,
        )
        self.assertIn("recursive=True", TASKS)

    def test_shared_and_mcp_roles_use_the_same_policy_serialization(self):
        mcp_tasks = (ROOT / "roles/thunderbird_mcp/tasks/main.yml").read_text()
        shared_content = next(
            line.strip() for line in TASKS.splitlines() if line.strip().startswith("content:")
        )
        mcp_content = next(
            line.strip()
            for line in mcp_tasks.splitlines()
            if "thunderbird_mcp_policies_document | to_nice_json" in line
        )
        self.assertEqual(
            shared_content.replace("thunderbird_policies_document", "POLICIES"),
            mcp_content.replace("thunderbird_mcp_policies_document", "POLICIES"),
        )


if __name__ == "__main__":
    unittest.main()
