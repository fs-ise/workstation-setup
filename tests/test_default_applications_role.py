"""Focused static checks for shared default-application ownership."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = (ROOT / "roles/default_applications/defaults/main.yml").read_text(encoding="utf-8")
TASKS = (ROOT / "roles/default_applications/tasks/main.yml").read_text(encoding="utf-8")


class DefaultApplicationsRoleTests(unittest.TestCase):
    def test_personal_default_choices_are_not_enforced(self):
        for fragment in (
            "text/plain",
            "application/json",
            "application/pdf",
            "Google Chrome",
            "x-scheme-handler/http",
            "x-scheme-handler/https",
            "Thunderbird",
            "message/rfc822",
            "x-scheme-handler/mailto",
        ):
            self.assertNotIn(fragment, DEFAULTS)

    def test_research_and_format_associations_remain(self):
        for fragment in (
            "text/x-quarto-markdown",
            "text/markdown",
            "text/x-python",
            "text/x-tex",
            "application/vnd.sqlite3",
        ):
            self.assertIn(fragment, DEFAULTS)

    def test_onlyoffice_owns_office_document_associations(self):
        self.assertIn("org.onlyoffice.desktopeditors.desktop", DEFAULTS)
        for mime_type in (
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.oasis.opendocument.text",
            "application/vnd.oasis.opendocument.spreadsheet",
            "application/vnd.oasis.opendocument.presentation",
            "application/rtf",
        ):
            self.assertIn(mime_type, DEFAULTS)
        self.assertNotIn("libreoffice-", DEFAULTS.lower())

    def test_role_still_validates_and_configures_declared_associations(self):
        for task in (
            "Find installed desktop entries",
            "Require expected desktop entries",
            "Configure default applications",
            "Verify qmd MIME recognition",
        ):
            self.assertIn(f"- name: {task}", TASKS)


if __name__ == "__main__":
    unittest.main()
