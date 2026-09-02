"""Checks for the workstation/cloud role boundary."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = (ROOT / "playbooks/lab-stack.yml").read_text(encoding="utf-8")
CLOUD = (ROOT / "playbooks/cloud-stack.yml").read_text(encoding="utf-8")
INSTALL_DOCS = (ROOT / "docs/install_software.qmd").read_text(encoding="utf-8")
CLOUD_DOCS = (ROOT / "docs/cloud_setup.qmd").read_text(encoding="utf-8")


class StackPlaybookTests(unittest.TestCase):
    def test_workstation_includes_desktop_apps(self):
        self.assertIn("- role: desktop_apps", LAB)

    def test_cloud_reuses_server_oriented_roles(self):
        for role in (
            "preflight", "baseline", "git_tools", "docker", "languagetool",
            "quarto", "latex", "r",
        ):
            self.assertIn(f"- role: {role}", CLOUD)

    def test_cloud_excludes_desktop_roles(self):
        for role in (
            "desktop_apps", "desktop_gnome", "default_applications", "chrome",
            "ocrmypdf", "grobid",
            "dropbox", "keepassxc", "nemo", "obsidian", "okular", "onlyoffice",
            "rstudio", "teams_for_linux", "thunderbird", "virtualbox", "vscode",
        ):
            self.assertNotIn(f"- role: {role}", CLOUD)
        self.assertIn("latex_additional_packages: []", CLOUD)

    def test_cloud_instructions_have_a_separate_reference_page(self):
        self.assertNotIn("playbooks/cloud-stack.yml", INSTALL_DOCS)
        self.assertIn("playbooks/lab-stack.yml", INSTALL_DOCS)
        self.assertIn("playbooks/cloud-stack.yml", CLOUD_DOCS)
        self.assertIn("OCRmyPDF and GROBID", CLOUD_DOCS)


if __name__ == "__main__":
    unittest.main()
