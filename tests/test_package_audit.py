"""Integration checks for role-derived DNF package auditing."""

import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PackageAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = (ROOT / "group_vars/all/package_audit.yml").read_text(encoding="utf-8")

        def values_under(key):
            section = text.split(f"\n{key}:\n", 1)[1].split("\n\n", 1)[0]
            return [
                line.removeprefix("  - ").strip("'")
                for line in section.splitlines()
                if line.startswith("  - ")
            ]

        cls.allowlist = values_under("package_audit_allowlist")
        cls.patterns = values_under("package_audit_allowlist_patterns")

    def is_allowed(self, package):
        return package in self.allowlist or any(
            re.match(pattern, package) for pattern in self.patterns
        )

    def test_comprehensive_manifest_was_removed(self):
        settings = (ROOT / "group_vars/all/package_audit.yml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("\npackage_audit_managed_packages:", settings)
        self.assertIn("\npackage_audit_allowlist:", settings)
        self.assertIn("\npackage_audit_allowlist_patterns:", settings)

    def test_every_dnf_installing_role_declares_owned_packages(self):
        missing = []
        for task_file in sorted((ROOT / "roles").glob("*/tasks/*.yml")):
            text = task_file.read_text(encoding="utf-8")
            if "ansible.builtin.dnf:" not in text or "state: present" not in text:
                continue
            role = task_file.relative_to(ROOT / "roles").parts[0]
            defaults_file = ROOT / "roles" / role / "defaults/main.yml"
            defaults = (
                defaults_file.read_text(encoding="utf-8")
                if defaults_file.exists()
                else ""
            )
            if f"\n{role}_managed_dnf_packages:" not in defaults:
                missing.append(role)
        self.assertEqual([], sorted(set(missing)))

    @unittest.skipUnless(
        shutil.which("ansible-playbook"), "ansible-playbook unavailable"
    )
    def test_ansible_discovers_and_derives_role_packages(self):
        for playbook in (
            "tests/playbooks/package-audit-shared-only.yml",
            "tests/playbooks/package-audit-derivation.yml",
        ):
            with self.subTest(playbook=playbook):
                result = subprocess.run(
                    [
                        "ansible-playbook",
                        "-i",
                        "tests/inventory/hosts.yml",
                        playbook,
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    @unittest.skipUnless(
        shutil.which("ansible-playbook"), "ansible-playbook unavailable"
    )
    def test_invalid_extra_roles_path_fails_clearly(self):
        result = subprocess.run(
            [
                "ansible-playbook",
                "-i",
                "tests/inventory/hosts.yml",
                "tests/playbooks/package-audit-invalid-path.yml",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        self.assertNotEqual(0, result.returncode, output)
        self.assertIn("is missing or is not a directory", output)

    def test_overlay_extension_defaults_are_empty(self):
        settings = (ROOT / "group_vars/all/package_audit.yml").read_text(
            encoding="utf-8"
        )
        for variable in (
            "package_audit_extra_roles_paths",
            "package_audit_extra_managed_dnf_packages",
            "package_audit_extra_allowlist",
            "package_audit_extra_allowlist_patterns",
        ):
            self.assertIn(f"\n{variable}: []", settings)

    def test_genuinely_unmanaged_package_remains_a_finding(self):
        detected = ["git", "manual-lab-package", " git ", "git"]
        managed = ["git", "python3", "git"]
        allowlist = ["local-exception"]
        normalized_detected = sorted({item.strip() for item in detected})
        unmanaged = sorted(set(normalized_detected) - set(managed) - set(allowlist))
        self.assertEqual(["manual-lab-package"], unmanaged)

    def test_unmanaged_package_failure_formats_packages_as_yaml_lines(self):
        playbook = (ROOT / "playbooks/audit-unmanaged-packages.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "package_audit_unmanaged | to_nice_yaml(indent=2) | trim | indent(2, true)",
            playbook,
        )
        self.assertNotIn("package_audit_unmanaged | join(", playbook)

    def test_expected_fedora_system_packages_remain_allowed(self):
        expected = [
            "fedora-release-workstation",
            "gnome-control-center",
            "kernel-modules-extra",
            "libgcc",
            "perl-interpreter",
        ]
        self.assertEqual(
            [], [package for package in expected if not self.is_allowed(package)]
        )

    def test_broad_prefixes_do_not_hide_manual_packages(self):
        manually_installed = [
            "fedora-third-party-tool",
            "gnome-lab-utility",
            "kernel-debugger-pro",
            "librewolf",
            "perl-my-lab-script",
        ]
        self.assertEqual(
            [], [package for package in manually_installed if self.is_allowed(package)]
        )

    def test_known_overbroad_patterns_are_not_configured(self):
        broad_patterns = {"^lib", "^perl", "^gnome-", "^fedora-", "^kernel"}
        self.assertTrue(broad_patterns.isdisjoint(self.patterns))

    def test_obsolete_baseline_packages_are_not_allowlisted(self):
        self.assertTrue({"gnome-terminal", "libxslt-devel"}.isdisjoint(self.allowlist))

    def test_nodejs_role_packages_and_dependencies_are_not_allowlisted(self):
        nodejs_packages = {
            "nodejs22-bin",
            "nodejs22-docs",
            "nodejs22-full-i18n",
            "nodejs22-libs",
            "nodejs22-npm",
            "nodejs22-npm-bin",
        }
        self.assertTrue(nodejs_packages.isdisjoint(self.allowlist))


if __name__ == "__main__":
    unittest.main()
