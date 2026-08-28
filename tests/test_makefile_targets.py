import os
import subprocess
import tempfile
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

    def run_update_base_with_git_state(self, symbolic_ref_status: int):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            bin_path = temporary_path / "bin"
            bin_path.mkdir()
            log_path = temporary_path / "commands.log"

            git_script = f"""#!/bin/sh
echo "git $*" >> "$COMMAND_LOG"
if [ "$1 $2 $3" = "symbolic-ref -q HEAD" ]; then
    exit {symbolic_ref_status}
fi
exit 0
"""
            command_script = """#!/bin/sh
echo "$(basename "$0") $*" >> "$COMMAND_LOG"
exit 0
"""
            for command, script in {
                "git": git_script,
                "ansible-galaxy": command_script,
                "ansible-playbook": command_script,
                "sudo": command_script,
                "flatpak": command_script,
            }.items():
                command_path = bin_path / command
                command_path.write_text(script)
                command_path.chmod(0o755)

            environment = os.environ.copy()
            environment["PATH"] = f"{bin_path}:{environment['PATH']}"
            environment["COMMAND_LOG"] = str(log_path)
            result = subprocess.run(
                ["make", "--no-print-directory", "update-base"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env=environment,
            )
            commands = log_path.read_text() if log_path.exists() else ""
            return result, commands

    def test_update_base_pulls_and_continues_on_branch(self):
        result, commands = self.run_update_base_with_git_state(0)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("git pull --ff-only", commands)
        self.assertIn("sudo dnf upgrade --refresh", commands)
        self.assertIn("flatpak update", commands)
        self.assertIn("ansible-galaxy collection install", commands)
        self.assertIn("ansible-playbook -i inventory", commands)

    def test_update_base_skips_pull_and_continues_on_detached_head(self):
        result, commands = self.run_update_base_with_git_state(1)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("git pull", commands)
        self.assertIn("Skipping Git update: checkout is detached", result.stdout)
        self.assertIn("sudo dnf upgrade --refresh", commands)
        self.assertIn("flatpak update", commands)
        self.assertIn("ansible-galaxy collection install", commands)
        self.assertIn("ansible-playbook -i inventory", commands)

    def test_update_base_does_not_suppress_other_git_errors(self):
        result, commands = self.run_update_base_with_git_state(2)

        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("git pull", commands)
        self.assertNotIn("sudo dnf upgrade --refresh", commands)
        self.assertNotIn("flatpak update", commands)


if __name__ == "__main__":
    unittest.main()
