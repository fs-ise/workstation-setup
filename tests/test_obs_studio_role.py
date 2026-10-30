"""Focused ownership checks for the OBS Studio Flatpak role."""

import getpass
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ObsStudioRoleTests(unittest.TestCase):
    def test_role_installs_apps_and_remote_for_target_user(self):
        defaults = (ROOT / "roles/obs_studio/defaults/main.yml").read_text()
        tasks = (ROOT / "roles/obs_studio/tasks/flatpak_install.yml").read_text()

        self.assertIn("obs_studio_flatpak_id: com.obsproject.Studio", defaults)
        self.assertIn("obs_studio_plugin_flatpak_id: com.obsproject.Studio.Plugin.BackgroundRemoval", defaults)
        self.assertIn("community.general.flatpak_remote:", tasks)
        self.assertIn("community.general.flatpak:", tasks)
        self.assertIn("- flatpak\n      - install\n      - --user", tasks)
        self.assertGreaterEqual(tasks.count('become_user: "{{ target_user }}"'), 5)
        self.assertIn("method: user", tasks)

    def test_plugin_only_install_does_not_satisfy_obs_install_condition(self):
        tasks = (ROOT / "roles/obs_studio/tasks/flatpak_install.yml").read_text()

        self.assertIn("obs_studio_flatpak_id not in obs_studio_installed.stdout_lines", tasks)
        plugin_only = ["com.obsproject.Studio.Plugin.BackgroundRemoval"]
        self.assertNotIn("com.obsproject.Studio", plugin_only)
        self.assertIn("Verify user-level OBS Studio installation", tasks)
        self.assertIn("Verify user-level Background Removal installation", tasks)
        self.assertEqual(tasks.count("      - info\n      - --user"), 2)

    @unittest.skipUnless(shutil.which("ansible-playbook"), "Ansible is not installed")
    def test_plugin_only_install_is_repaired_and_second_run_is_unchanged(self):
        user = getpass.getuser()
        if subprocess.run(
            ["sudo", "-n", "-u", user, "true"],
            check=False,
            capture_output=True,
        ).returncode != 0:
            self.skipTest("Passwordless privilege escalation to the target user is unavailable")

        with tempfile.TemporaryDirectory(prefix="obs-flatpak-test-") as directory:
            test_dir = Path(directory)
            fake_bin = test_dir / "bin"
            fake_bin.mkdir()
            state_file = test_dir / "installed-apps"
            state_file.write_text("com.obsproject.Studio.Plugin.BackgroundRemoval\n")
            fake_flatpak = fake_bin / "flatpak"
            fake_flatpak.write_text(
                """#!/usr/bin/env python3
import os
import sys
from pathlib import Path

state = Path(os.environ['FAKE_FLATPAK_STATE'])
args = sys.argv[1:]
installed = state.read_text().splitlines()

if args == ['--version']:
    print('Flatpak 1.16.0')
elif args and args[0] == 'remote-list':
    print('flathub')
elif args and args[0] == 'list':
    print('\\n'.join(installed))
elif args and args[0] == 'install':
    app_id = args[-1]
    if app_id not in installed:
        state.write_text('\\n'.join(installed + [app_id]) + '\\n')
elif args and args[0] == 'info':
    sys.exit(0 if args[-1] in installed else 1)
else:
    raise SystemExit('Unexpected fake Flatpak command: ' + repr(args))
"""
            )
            fake_flatpak.chmod(0o755)

            inventory = test_dir / "inventory"
            inventory.write_text("localhost ansible_connection=local\n")
            playbook = test_dir / "playbook.yml"
            playbook.write_text(
                """---
- name: Exercise the OBS user Flatpak installation tasks
  hosts: localhost
  connection: local
  gather_facts: true
  vars:
    target_user: """
                + json.dumps(user)
                + """
    obs_studio_flatpak_id: com.obsproject.Studio
    obs_studio_plugin_flatpak_id: com.obsproject.Studio.Plugin.BackgroundRemoval
  environment:
    PATH: """
                + json.dumps(
                    f"{fake_bin}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                )
                + """
    FAKE_FLATPAK_STATE: """
                + json.dumps(str(state_file))
                + """
  tasks:
    - name: Install and verify OBS user Flatpaks
      ansible.builtin.include_tasks: """
                + json.dumps(str(ROOT / "roles/obs_studio/tasks/flatpak_install.yml"))
                + "\n"
            )

            command = [
                "ansible-playbook",
                "-i",
                str(inventory),
                str(playbook),
            ]
            first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertIn("Install OBS Studio if its exact user Flatpak ID is missing", first.stdout)
            self.assertEqual(
                state_file.read_text().splitlines(),
                [
                    "com.obsproject.Studio.Plugin.BackgroundRemoval",
                    "com.obsproject.Studio",
                ],
            )

            second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            recap = second.stdout.split("PLAY RECAP", 1)[-1]
            self.assertRegex(recap, r"changed=0(?:\s|$)")

    def test_role_only_manages_flatpaks_not_an_obs_rpm(self):
        role_content = "".join(
            path.read_text()
            for path in (ROOT / "roles/obs_studio").rglob("*")
            if path.is_file()
        ).lower()

        self.assertNotIn("obs-studio", role_content)
        self.assertNotIn("package_facts", role_content)
        self.assertIn("flatpak:", role_content)

    def test_lab_stack_exposes_obs_tag(self):
        playbook = (ROOT / "playbooks/lab-stack.yml").read_text()
        self.assertEqual(playbook.count("- role: obs_studio"), 1)
        self.assertIn("tags: [obs]", playbook)


if __name__ == "__main__":
    unittest.main()
