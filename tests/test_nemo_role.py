"""Focused checks for nemo."""
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=(R/'roles/nemo/defaults/main.yml').read_text(); T=(R/'roles/nemo/tasks/main.yml').read_text(); B=(R/'roles/baseline/defaults/main.yml').read_text(); G=''.join(p.read_text() for p in (R/'roles/desktop_gnome').rglob('*.yml')); A=(R/'group_vars/all/package_audit.yml').read_text()
class Tests(unittest.TestCase):
 def test_owned_behavior(self):
  [self.assertIn(x,D) for x in ('nemo-fileroller','nemo-preview','show-image-thumbnails','<Super>e')]; self.assertIn('regex_findall',T); self.assertIn('| unique | list',T); self.assertIn('nemo_configure_preferences | bool',T); self.assertIn('nemo_configure_shortcut | bool',T)
 def test_terminal_is_managed_by_nemo(self):
  self.assertIn('  - nemo-terminal\n',D); self.assertIn('nemo_managed_dnf_packages: "{{ nemo_packages }}"',D); self.assertNotIn('  - nemo-terminal\n',A)
  self.assertIn('NemoTerminalProvider+NemoPython',D); self.assertIn('nemo_required_enabled_extensions',T)
  self.assertIn('difference(nemo_required_enabled_extensions)',T); self.assertIn('intersect(nemo_required_enabled_extensions)',T)
  self.assertNotIn('disabled-extensions "[]"',T)
 def test_terminal_enablement_preserves_other_disabled_extensions(self):
  disabled=['NemoTerminalProvider+NemoPython','UnrelatedProvider']; required=['NemoTerminalProvider+NemoPython']
  self.assertEqual(['UnrelatedProvider'],[provider for provider in disabled if provider not in required])
 def test_old_owners_slim_and_integrations_stay(self):
  [self.assertNotIn(x,B) for x in ('nemo-fileroller','nemo-preview')]; self.assertNotIn('org/nemo',G); self.assertNotIn("'<Super>e'",G)
  self.assertIn('.nemo_action',(R/'roles/ocrmypdf/tasks/main.yml').read_text()); self.assertIn('.nemo_action',(R/'roles/grobid/tasks/main.yml').read_text())

if __name__ == "__main__": unittest.main()
