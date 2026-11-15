"""Behavior tests for the read-only directory configuration audit."""

import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/audit_directories.py"
SPEC = importlib.util.spec_from_file_location("directory_audit", MODULE_PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class DirectoryAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.variables = AUDIT.required_variables()
        self.environment = {
            item["name"]: os.fspath(self.root / f"directory {index}")
            for index, item in enumerate(self.variables)
        }
        for path in self.environment.values():
            Path(path).mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_contract_contains_all_required_variables_once(self):
        expected = {
            "REPOS_DIR", "WORKSPACE_DIR", "NEXTCLOUD_DIR", "PERSONAL_DIR",
            "INBOX_DIR", "TICKLER_DIR", "WAITING_FOR_DIR", "ACTION_DIR",
            "WORK_PROJECTS_DIR", "TO_ARCHIVE_DIR", "SOMEDAY_DIR",
            "TEACHING_DIR", "TEACHING_THESES_DIR", "CHECKLISTS_DIR", "REVIEWS_DIR",
        }
        names = [item["name"] for item in self.variables]
        self.assertEqual(expected, set(names))
        self.assertEqual(len(expected), len(names))
        self.assertTrue(all(name.endswith("_DIR") for name in names))

    def test_valid_absolute_directories_including_spaces(self):
        results = AUDIT.audit_directories(self.environment)
        self.assertTrue(all(error is None for _, _, error in results))
        self.assertIn(" ", results[0][1])

    def test_missing_and_empty_variables_are_distinguished(self):
        environment = self.environment.copy()
        del environment["REPOS_DIR"]
        environment["WORKSPACE_DIR"] = ""
        results = {name: error for name, _, error in AUDIT.audit_directories(environment)}
        self.assertEqual("Not defined", results["REPOS_DIR"])
        self.assertEqual("Empty value", results["WORKSPACE_DIR"])

    def test_relative_and_nonexistent_paths_are_rejected(self):
        environment = self.environment.copy()
        environment["REPOS_DIR"] = "relative/repos"
        environment["WORKSPACE_DIR"] = os.fspath(self.root / "absent")
        results = {name: error for name, _, error in AUDIT.audit_directories(environment)}
        self.assertEqual("Path is not absolute", results["REPOS_DIR"])
        self.assertEqual("Directory does not exist", results["WORKSPACE_DIR"])

    def test_inaccessible_directory_is_reported(self):
        with patch.object(AUDIT.os, "access", return_value=False):
            results = AUDIT.audit_directories(self.environment)
        self.assertTrue(all(error == "Directory is not accessible by the target user" for _, _, error in results))

    def test_report_only_and_strict_modes(self):
        environment = os.environ.copy()
        for item in self.variables:
            environment.pop(item["name"], None)
        environment.pop(AUDIT.STRICT_ENV, None)
        report = subprocess.run(
            ["python3", os.fspath(MODULE_PATH)], env=environment,
            capture_output=True, text=True,
        )
        self.assertEqual(0, report.returncode)
        self.assertIn("WARNING:", report.stdout)
        self.assertIn("Not defined", report.stdout)
        environment[AUDIT.STRICT_ENV] = "true"
        strict = subprocess.run(
            ["python3", os.fspath(MODULE_PATH)], env=environment,
            capture_output=True, text=True,
        )
        self.assertEqual(1, strict.returncode)

    def test_reads_environment_from_invoking_process_not_ansible_become(self):
        result = AUDIT.audit_directories(self.environment)
        self.assertEqual(self.environment["REPOS_DIR"], result[0][1])
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/audit_directories.py", makefile)
        self.assertNotIn("become", makefile)

    def test_make_audit_preserves_existing_package_audit(self):
        result = subprocess.run(
            ["make", "--dry-run", "audit"], cwd=ROOT,
            capture_output=True, text=True, check=True,
        )
        self.assertIn("make audit-directories", result.stdout)
        self.assertIn("make audit-packages", result.stdout)
        self.assertIn("playbooks/audit-unmanaged-packages.yml", result.stdout)


if __name__ == "__main__":
    unittest.main()
