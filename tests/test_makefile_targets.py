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

    def test_configure_sets_up_dependencies_before_lab_stack(self):
        output = self.dry_run("configure")
        bootstrap = "sudo dnf -y install ansible-core python3 python3-pip dnf-plugins-core"
        galaxy = "ansible-galaxy collection install -r requirements.yml --upgrade"

        self.assertIn(bootstrap, output)
        self.assertIn(galaxy, output)
        self.assertIn("make lab-stack", output)
        self.assertIn("playbooks/lab-stack.yml", output)
        self.assertLess(output.index(bootstrap), output.index(galaxy))
        self.assertLess(output.index(galaxy), output.index("playbooks/lab-stack.yml"))

    def test_setup_combines_prerequisites_and_galaxy_dependencies(self):
        output = self.dry_run("setup")
        self.assertIn("ansible-core", output)
        self.assertIn("requirements.yml", output)

    def test_install_is_a_backward_compatible_configure_alias(self):
        output = self.dry_run("install")
        self.assertIn("ansible-core", output)
        self.assertIn("playbooks/lab-stack.yml", output)

    def test_audit_delegates_to_package_audit(self):
        output = self.dry_run("audit")
        self.assertIn("make audit-packages", output)
        self.assertIn("playbooks/audit-unmanaged-packages.yml", output)

    def test_update_composes_public_targets(self):
        output = self.dry_run("update")
        self.assertIn("make update-base", output)
        self.assertIn("make configure", output)
        self.assertIn("make audit", output)
        self.assertEqual(output.count("ansible-galaxy collection install"), 1)
        self.assertEqual(output.count("playbooks/lab-stack.yml"), 1)
        self.assertEqual(output.count("playbooks/audit-unmanaged-packages.yml"), 1)

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

    def run_backup(self, home_path: Path, flatpak_script: str):
        bin_path = home_path.parent / "bin"
        bin_path.mkdir()
        flatpak_path = bin_path / "flatpak"
        flatpak_path.write_text(flatpak_script)
        flatpak_path.chmod(0o755)

        environment = os.environ.copy()
        environment["HOME"] = str(home_path)
        environment["PATH"] = f"{bin_path}:{environment['PATH']}"
        environment["COMMAND_LOG"] = str(home_path.parent / "commands.log")
        return subprocess.run(
            [
                "make",
                "--no-print-directory",
                "backup",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_backup_preserves_user_files_and_launches_vorta(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            home_path = temporary_path / "home"
            nextcloud_path = home_path / "Nextcloud"
            nextcloud_path.mkdir(parents=True)
            trash_path = home_path / ".local" / "share" / "Trash"
            trash_path.mkdir(parents=True)

            thumbs_file = nextcloud_path / "Thumbs.db"
            encrypted_thumbs_file = nextcloud_path / "Thumbs.db:encryptable"
            trash_file = trash_path / "keep.txt"
            thumbs_file.write_text("keep")
            encrypted_thumbs_file.write_text("keep")
            trash_file.write_text("keep")

            result = self.run_backup(
                home_path,
                """#!/bin/sh
echo "flatpak $*" >> "$COMMAND_LOG"
case "$1" in
  info) exit 0 ;;
  ps) exit 0 ;;
  run) exit 0 ;;
esac
exit 1
""",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(thumbs_file.exists())
            self.assertTrue(encrypted_thumbs_file.exists())
            self.assertTrue(trash_file.exists())
            self.assertIn("[TODO] nextcloud-sync-check", result.stdout)
            self.assertIn("[TODO] git-repo-check", result.stdout)
            commands = (temporary_path / "commands.log").read_text()
            self.assertIn("flatpak info com.borgbase.Vorta", commands)
            self.assertIn("flatpak run com.borgbase.Vorta", commands)

    def test_backup_does_not_launch_a_second_vorta_instance(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            home_path = temporary_path / "home"
            (home_path / ".local" / "share" / "Trash").mkdir(parents=True)

            result = self.run_backup(
                home_path,
                """#!/bin/sh
echo "flatpak $*" >> "$COMMAND_LOG"
case "$1" in
  info) exit 0 ;;
  ps) echo com.borgbase.Vorta; exit 0 ;;
  run) exit 99 ;;
esac
exit 1
""",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("already running", result.stdout)
            commands = (temporary_path / "commands.log").read_text()
            self.assertNotIn("flatpak run", commands)


if __name__ == "__main__":
    unittest.main()
