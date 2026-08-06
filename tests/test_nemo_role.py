"""Focused checks for nemo."""
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=(R/'roles/nemo/defaults/main.yml').read_text(); T=(R/'roles/nemo/tasks/main.yml').read_text(); B=(R/'roles/baseline/defaults/main.yml').read_text(); G=''.join(p.read_text() for p in (R/'roles/desktop_gnome').rglob('*.yml'))
class Tests(unittest.TestCase):
 def test_owned_behavior(self):
  [self.assertIn(x,D) for x in ('nemo-fileroller','nemo-preview','show-image-thumbnails','<Super>e')]; self.assertIn('regex_findall',T); self.assertIn('| unique | list',T); self.assertIn('nemo_configure_preferences | bool',T); self.assertIn('nemo_configure_shortcut | bool',T)
 def test_old_owners_slim_and_integrations_stay(self):
  [self.assertNotIn(x,B) for x in ('nemo-fileroller','nemo-preview')]; self.assertNotIn('org/nemo',G); self.assertNotIn("'<Super>e'",G)
  self.assertIn('.nemo_action',(R/'roles/ocrmypdf/tasks/main.yml').read_text()); self.assertIn('.nemo_action',(R/'roles/grobid/tasks/main.yml').read_text())

if __name__ == "__main__": unittest.main()
