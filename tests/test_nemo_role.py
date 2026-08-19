"""Focused checks for the shared Nemo installation role."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = (ROOT / "roles/nemo/defaults/main.yml").read_text(encoding="utf-8")
TASKS = (ROOT / "roles/nemo/tasks/main.yml").read_text(encoding="utf-8")


class NemoRoleTests(unittest.TestCase):
    def test_role_keeps_generic_nemo_capabilities(self):
        for package in ("nemo", "nemo-fileroller", "nemo-preview"):
            self.assertIn(f"  - {package}\n", DEFAULTS)
        self.assertIn('nemo_managed_dnf_packages: "{{ nemo_packages }}"', DEFAULTS)
        self.assertIn("Install Nemo", TASKS)

    def test_role_does_not_manage_personal_preferences_or_actions(self):
        for fragment in (
            "<Super>e",
            "open-ptyxis",
            "actions-tree.json",
            "show-image-thumbnails",
            "advanced-permissions",
            "nemo_configure_preferences",
        ):
            self.assertNotIn(fragment, DEFAULTS + TASKS)

    def test_application_specific_integrations_remain_separate(self):
        for role in ("ocrmypdf", "grobid"):
            tasks = (ROOT / f"roles/{role}/tasks/main.yml").read_text(encoding="utf-8")
            self.assertIn(".nemo_action", tasks)


if __name__ == "__main__":
    unittest.main()
