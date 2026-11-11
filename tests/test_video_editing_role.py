"""Focused checks for the FFmpeg and Kdenlive role."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = (ROOT / "roles/video_editing/defaults/main.yml").read_text(encoding="utf-8")
TASKS = (ROOT / "roles/video_editing/tasks/main.yml").read_text(encoding="utf-8")
PLAYBOOK = (ROOT / "playbooks/lab-stack.yml").read_text(encoding="utf-8")
DOCS = (ROOT / "docs/video_editing.qmd").read_text(encoding="utf-8")
SOFTWARE_DOCS = (ROOT / "docs/software.qmd").read_text(encoding="utf-8")


class VideoEditingRoleTests(unittest.TestCase):
    def test_role_installs_and_owns_ffmpeg_and_kdenlive_packages(self):
        self.assertIn("video_editing_packages:\n  - ffmpeg-free\n  - kdenlive", DEFAULTS)
        self.assertIn(
            'video_editing_managed_dnf_packages: "{{ video_editing_packages }}"',
            DEFAULTS,
        )
        self.assertIn("ansible.builtin.dnf:", TASKS)
        self.assertIn('name: "{{ video_editing_packages }}"', TASKS)
        self.assertIn("state: present", TASKS)

    def test_lab_stack_exposes_video_editing_tag(self):
        self.assertIn("- role: video_editing\n      tags: [video_editing]", PLAYBOOK)

    def test_documentation_lists_run_command_checks_and_software_index(self):
        self.assertIn("--tags video_editing", DOCS)
        self.assertIn("ffmpeg -version", DOCS)
        self.assertIn("kdenlive --version", DOCS)
        self.assertIn("[Video editing](video_editing.qmd)", SOFTWARE_DOCS)


if __name__ == "__main__":
    unittest.main()
