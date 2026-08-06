"""Focused checks for thunderbird_mcp."""
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=(R/'roles/thunderbird_mcp/defaults/main.yml').read_text(); T=(R/'roles/thunderbird_mcp/tasks/main.yml').read_text(); BD=(R/'roles/thunderbird/defaults/main.yml').read_text(); BT=(R/'roles/thunderbird/tasks/main.yml').read_text(); P=(R/'playbooks/lab-stack.yml').read_text()
class Tests(unittest.TestCase):
 def test_defaults_and_security(self):
  self.assertIn('"0.7.4"',D); self.assertIn('https://github.com/TKasperczyk/thunderbird-mcp.git',D); self.assertIn('installation_mode: normal_installed',D); self.assertIn('mode: "0600"',T); self.assertIn('mode: "0755"',T); self.assertGreaterEqual(T.count('thunderbird_mcp_enabled | bool'),8); self.assertIn('thunderbird_mcp_write_client_fragment | bool',T)
 def test_safe_policy_merge(self):
  self.assertIn("if thunderbird_mcp_policies_stat.stat.exists else {'policies': {}}",T); self.assertIn('ExtensionSettings',T); self.assertIn('combine',T); self.assertIn('mode: "0644"',T)
 def test_base_and_tags(self):
  self.assertNotIn('thunderbird_mcp',BD+BT); self.assertIn('tags: [thunderbird, thunderbird_mcp]',P); self.assertIn('role: thunderbird_mcp',P)

if __name__ == "__main__": unittest.main()
