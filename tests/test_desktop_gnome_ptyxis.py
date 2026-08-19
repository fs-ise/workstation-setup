import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "roles/desktop_gnome/defaults/main.yml"
TASKS_PATH = ROOT / "roles/desktop_gnome/tasks/main.yml"


class DesktopGnomePtyxisShortcutsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defaults = DEFAULTS_PATH.read_text()
        cls.tasks = TASKS_PATH.read_text()

    def test_both_shortcuts_explicitly_open_a_new_window(self):
        self.assertIn("binding: <Control><Alt>t", self.defaults)
        self.assertIn("binding: <Super>t", self.defaults)
        self.assertEqual(2, self.defaults.count("command: ptyxis --new-window"))
        self.assertIn("custom0/", self.defaults)
        self.assertIn("ptyxis-super-t/", self.defaults)

    def test_registered_paths_are_merged_with_existing_paths(self):
        self.assertIn("desktop_gnome_custom_shortcuts_read.stdout", self.tasks)
        self.assertIn("map(attribute='path')", self.tasks)
        self.assertIn("| unique | list | to_json", self.tasks)


if __name__ == "__main__":
    unittest.main()
