"""Focused checks for git_tools."""
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=(R/'roles/git_tools/defaults/main.yml').read_text(); T=(R/'roles/git_tools/tasks/main.yml').read_text(); B=''.join(p.read_text() for p in (R/'roles/baseline').rglob('*.yml'))
class Tests(unittest.TestCase):
 def test_packages_and_config(self):
  [self.assertIn(x,D) for x in ('git-lfs','gitk','log.date','push.autoSetupRemote','core.editor','init.defaultBranch')]
  self.assertIn('community.general.git_config',T); self.assertIn('become_user: "{{ target_user }}"',T); self.assertIn('git_tools_packages | length > 0',T)
 def test_baseline_slim(self):
  self.assertNotIn('git-lfs',B); self.assertNotIn('gitk',B); self.assertNotIn('community.general.git_config',B)

if __name__ == "__main__": unittest.main()
