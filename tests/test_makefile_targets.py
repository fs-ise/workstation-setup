import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MakefileTargetTests(unittest.TestCase):
    def dry_run(self, target: str) -> str:
        result = subprocess.run(
            ["make", "--dry-run", target],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def test_install_delegates_to_lab_stack(self):
        output = self.dry_run("install")
        self.assertIn("make lab-stack", output)
        self.assertIn("playbooks/lab-stack.yml", output)

    def test_audit_delegates_to_package_audit(self):
        output = self.dry_run("audit")
        self.assertIn("make audit-packages", output)
        self.assertIn("playbooks/audit-unmanaged-packages.yml", output)

    def test_update_composes_public_targets(self):
        output = self.dry_run("update")
        self.assertIn("make update-base", output)
        self.assertIn("make install", output)
        self.assertIn("make audit", output)


if __name__ == "__main__":
    unittest.main()
