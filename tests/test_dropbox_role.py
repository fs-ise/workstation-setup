"""Focused checks for dropbox."""
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=(R/'roles/dropbox/defaults/main.yml').read_text(); T=(R/'roles/dropbox/tasks/main.yml').read_text(); G=(R/'roles/desktop_gnome/tasks/main.yml').read_text().lower()
class Tests(unittest.TestCase):
 def test_owned_and_conditional(self):
  [self.assertIn(x,D) for x in ('dropbox','nautilus-dropbox')]; self.assertIn('repo_rpmfusion',T); self.assertGreaterEqual(T.count('dropbox_install | bool'),2); self.assertGreaterEqual(T.count('dropbox_packages | length > 0'),2); self.assertNotIn('failed_when: false',T)
 def test_desktop_slim(self):
  self.assertNotIn('dropbox',G); self.assertNotIn('repo_rpmfusion',G)

if __name__ == "__main__": unittest.main()
