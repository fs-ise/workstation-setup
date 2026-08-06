"""Focused checks for backup_borg."""
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=(R/'roles/backup_borg/defaults/main.yml').read_text(); T=(R/'roles/backup_borg/tasks/main.yml').read_text(); B=(R/'roles/baseline/defaults/main.yml').read_text(); G=(R/'roles/desktop_gnome/tasks/main.yml').read_text()
class Tests(unittest.TestCase):
 def test_ownership(self):
  self.assertIn('borgbackup',D); self.assertIn('com.borgbase.Vorta',D); self.assertIn('backup_borg_install_vorta',T); self.assertIn('backup_borg_configure_flathub | bool',T); self.assertIn('backup_borg_packages | length > 0',T)
  self.assertNotIn('borgbackup',B); self.assertNotIn('com.borgbase.Vorta',G)

if __name__ == "__main__": unittest.main()
