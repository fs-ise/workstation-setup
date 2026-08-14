"""Focused checks for the Nemo role and its action-layout merge helper."""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = (ROOT / "roles/nemo/defaults/main.yml").read_text(encoding="utf-8")
TASKS = (ROOT / "roles/nemo/tasks/main.yml").read_text(encoding="utf-8")
ACTION_HELPER_PATH = ROOT / "roles/nemo/files/merge_nemo_action_layout.py"
PTYXIS_HELPER_PATH = ROOT / "roles/nemo/files/open-ptyxis-here.py"
AUDIT = (ROOT / "group_vars/all/package_audit.yml").read_text(encoding="utf-8")

SPEC = importlib.util.spec_from_file_location("nemo_action_layout", ACTION_HELPER_PATH)
ACTION_LAYOUT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ACTION_LAYOUT)

PTYXIS_SPEC = importlib.util.spec_from_file_location("open_ptyxis_here", PTYXIS_HELPER_PATH)
PTYXIS_HELPER = importlib.util.module_from_spec(PTYXIS_SPEC)
PTYXIS_SPEC.loader.exec_module(PTYXIS_HELPER)


class NemoRoleTests(unittest.TestCase):
    def test_packages_migrate_from_nemo_terminal_to_managed_ptyxis(self):
        desired_packages = DEFAULTS.split("nemo_packages:", 1)[1].split(
            "nemo_obsolete_packages:", 1
        )[0]
        self.assertNotIn("nemo-terminal", desired_packages)
        self.assertIn('nemo_action_package: ptyxis', DEFAULTS)
        self.assertIn('- "{{ nemo_action_package }}"', desired_packages)
        self.assertIn('nemo_managed_dnf_packages: "{{ nemo_packages }}"', DEFAULTS)
        self.assertNotIn("  - ptyxis\n", AUDIT)
        self.assertIn("nemo_obsolete_packages", TASKS)
        self.assertIn("state: absent", TASKS)
        self.assertIn("  - nemo-terminal\n", DEFAULTS)

    def test_embedded_terminal_enablement_is_removed(self):
        for obsolete in (
            "NemoTerminalProvider+NemoPython",
            "nemo_configure_extensions",
            "nemo_plugins_schema",
            "nemo_disabled_extensions_key",
            "nemo_required_enabled_extensions",
        ):
            self.assertNotIn(obsolete, DEFAULTS)
            self.assertNotIn(obsolete, TASKS)

    def test_ptyxis_action_and_layout_binding_are_installed(self):
        for fragment in (
            "%P",
            "nemo_ptyxis_helper_path",
            "open-ptyxis-here.py",
            'mode: "0755"',
            "Quote=double",
        ):
            self.assertIn(fragment, DEFAULTS + TASKS)
        self.assertIn("open-ptyxis.nemo_action", DEFAULTS)
        self.assertIn("actions-tree.json", DEFAULTS)
        self.assertIn("nemo_action_shortcut: F8", DEFAULTS)
        self.assertIn("merge_nemo_action_layout.py", TASKS)

    def test_ptyxis_action_uses_helper_and_nemo_native_quoting(self):
        self.assertIn(
            'nemo_action_command: "{{ nemo_ptyxis_helper_path }} %P"',
            DEFAULTS,
        )
        self.assertIn("Quote=double", TASKS)
        self.assertNotIn("--working-directory", DEFAULTS + TASKS)

    def test_ptyxis_helper_launches_with_special_path_as_cwd(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory) / '#wait olm-signalling/test dir "\'$&'
            directory.mkdir(parents=True)

            with mock.patch.object(PTYXIS_HELPER.sys, "argv", ["helper", str(directory)]):
                with mock.patch.object(PTYXIS_HELPER.subprocess, "Popen") as popen:
                    self.assertEqual(0, PTYXIS_HELPER.main())

            popen.assert_called_once_with(
                ["ptyxis", "--new-window", "--", "bash"],
                cwd=directory.resolve(),
                start_new_session=True,
            )
            argv = popen.call_args.args[0]
            self.assertIsInstance(argv, list)
            self.assertNotIn(str(directory), argv)
            self.assertNotIn("shell", popen.call_args.kwargs)

    def test_merge_preserves_unrelated_action_metadata_and_order(self):
        layout = {
            "toplevel": [
                {
                    "uuid": "custom.nemo_action",
                    "type": "action",
                    "user-label": "My label",
                    "user-icon": "starred",
                    "accelerator": "F7",
                },
                {
                    "label": "Research",
                    "type": "submenu",
                    "children": [
                        {
                            "uuid": "nested.nemo_action",
                            "type": "action",
                            "user-label": "Nested",
                            "accelerator": "F6",
                        }
                    ],
                },
            ],
            "layout-version": 1,
        }
        original_first = layout["toplevel"][0].copy()
        merged = ACTION_LAYOUT.merge_layout(layout, "open-ptyxis.nemo_action", "F8")
        self.assertEqual(original_first, merged["toplevel"][0])
        self.assertEqual("Research", merged["toplevel"][1]["label"])
        self.assertEqual("Nested", merged["toplevel"][1]["children"][0]["user-label"])
        self.assertEqual(1, merged["layout-version"])
        managed = merged["toplevel"][2]
        self.assertEqual("open-ptyxis.nemo_action", managed["uuid"])
        self.assertEqual("action", managed["type"])
        self.assertEqual("F8", managed["accelerator"])
        self.assertIsNone(managed["user-label"])
        self.assertIsNone(managed["user-icon"])
        self.assertNotIn("id", managed)

    def test_merge_migrates_legacy_id_and_preserves_managed_metadata(self):
        layout = {
            "toplevel": [
                {
                    "id": "open-ptyxis.nemo_action",
                    "type": "action",
                    "user-label": "Keep this label",
                    "user-icon": "utilities-terminal-symbolic",
                    "accelerator": "F9",
                },
            ]
        }
        managed = ACTION_LAYOUT.merge_layout(
            layout, "open-ptyxis.nemo_action", "F8"
        )["toplevel"][0]
        self.assertEqual("open-ptyxis.nemo_action", managed["uuid"])
        self.assertNotIn("id", managed)
        self.assertEqual("F8", managed["accelerator"])
        self.assertEqual("Keep this label", managed["user-label"])
        self.assertEqual("utilities-terminal-symbolic", managed["user-icon"])

    def test_merge_removes_duplicates_and_conflicting_f8_deterministically(self):
        layout = {
            "toplevel": [
                {
                    "uuid": "conflict.nemo_action",
                    "type": "action",
                    "user-label": "Keep conflict metadata",
                    "accelerator": "F8",
                },
                {
                    "uuid": "open-ptyxis.nemo_action",
                    "type": "action",
                    "user-label": "Keep this label",
                    "accelerator": "F9",
                },
                {"id": "open-ptyxis.nemo_action", "type": "action"},
            ]
        }
        merged = ACTION_LAYOUT.merge_layout(layout, "open-ptyxis.nemo_action", "F8")
        self.assertNotIn("accelerator", merged["toplevel"][0])
        self.assertEqual("Keep conflict metadata", merged["toplevel"][0]["user-label"])
        managed = [
            item
            for item in merged["toplevel"]
            if item.get("uuid") == "open-ptyxis.nemo_action"
        ]
        self.assertEqual(1, len(managed))
        self.assertEqual("F8", managed[0]["accelerator"])
        self.assertEqual("Keep this label", managed[0]["user-label"])
        self.assertNotIn("id", managed[0])

    def test_update_file_creates_layout_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".config/nemo/actions-tree.json"
            self.assertTrue(
                ACTION_LAYOUT.update_file(path, "open-ptyxis.nemo_action", "F8")
            )
            first_contents = path.read_text(encoding="utf-8")
            first_mtime = os.stat(path).st_mtime_ns
            self.assertFalse(
                ACTION_LAYOUT.update_file(path, "open-ptyxis.nemo_action", "F8")
            )
            self.assertEqual(first_contents, path.read_text(encoding="utf-8"))
            self.assertEqual(first_mtime, os.stat(path).st_mtime_ns)
            self.assertEqual(
                "F8", json.loads(first_contents)["toplevel"][0]["accelerator"]
            )
            self.assertNotIn("id", json.loads(first_contents)["toplevel"][0])

    def test_existing_nemo_integrations_and_shortcut_remain(self):
        self.assertIn("<Super>e", DEFAULTS)
        self.assertIn("regex_findall", TASKS)
        for role in ("ocrmypdf", "grobid"):
            role_tasks = (ROOT / f"roles/{role}/tasks/main.yml").read_text(encoding="utf-8")
            self.assertIn(".nemo_action", role_tasks)


if __name__ == "__main__":
    unittest.main()
