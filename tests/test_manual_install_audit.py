"""Behavior tests for the read-only manual installation scanner."""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/audit_manual_installations.py"
SPEC = importlib.util.spec_from_file_location("manual_audit", MODULE_PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class ManualInstallAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.bin = root / "usr-local-bin"
        self.opt = root / "opt"
        self.bin.mkdir()
        self.opt.mkdir()
        self.rpm = root / "rpm"
        self.rpm.write_text(
            "#!/bin/sh\ncase \"$4\" in *rpm-owned*) printf test-package; exit 0;; esac\nexit 1\n",
            encoding="utf-8",
        )
        self.rpm.chmod(0o755)

    def tearDown(self):
        self.temp.cleanup()

    def scan(self):
        return AUDIT.audit_paths([self.bin], self.opt, os.fspath(self.rpm))

    def test_rpm_owned_executable_is_not_flagged(self):
        (self.bin / "rpm-owned").touch()
        self.assertEqual([], self.scan())

    def test_regular_non_rpm_file_is_flagged(self):
        (self.bin / "manual-tool").touch()
        self.assertEqual("manual-tool", self.scan()[0]["name"])

    def test_symlink_into_opt_is_flagged_and_resolved(self):
        install = self.opt / "quarto-1.9.37"
        (install / "bin").mkdir(parents=True)
        target = install / "bin/quarto"
        target.touch()
        (self.bin / "quarto").symlink_to(target)
        findings = self.scan()
        link = next(item for item in findings if item["path"] == os.fspath(self.bin / "quarto"))
        self.assertEqual(os.fspath(target), link["target"])

    def test_exact_allowlist_ignores_manual_installation(self):
        (self.bin / "local-tool").touch()
        self.assertEqual([], AUDIT.apply_allowlists(self.scan(), ["local-tool"], []))

    def test_pattern_allowlist_ignores_manual_installation(self):
        (self.bin / "lab-tool").touch()
        self.assertEqual([], AUDIT.apply_allowlists(self.scan(), [], [r"^lab-"]))

    def test_broken_symlink_is_reported_without_error(self):
        link = self.bin / "missing-tool"
        link.symlink_to(self.opt / "missing/bin/tool")
        finding = self.scan()[0]
        self.assertTrue(finding["broken_symlink"])
        self.assertEqual(os.fspath(self.opt / "missing/bin/tool"), finding["target"])


if __name__ == "__main__":
    unittest.main()
