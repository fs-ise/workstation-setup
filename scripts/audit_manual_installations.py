#!/usr/bin/python3
"""Find high-signal filesystem installations that are not owned by RPM."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


def rpm_owner(path: Path, rpm_command: str = "rpm") -> str | None:
    """Return the owning RPM name, or None when RPM does not own the path."""
    result = subprocess.run(
        [rpm_command, "-qf", "--queryformat", "%{NAME}", os.fspath(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def normalized_name(path: Path) -> str:
    """Derive a stable recommendation key from an executable or /opt path."""
    name = path.name.lower()
    name = re.sub(r"[-_.]?v?\d+(?:[.-]\d+)*.*$", "", name)
    return re.sub(r"[^a-z0-9+_-]", "-", name).strip("-_") or path.name.lower()


def inspect_entry(path: Path, rpm_command: str = "rpm") -> dict[str, object] | None:
    """Describe an entry only when neither it nor its effective target is RPM-owned."""
    is_link = path.is_symlink()
    target = path.resolve(strict=False) if is_link else path
    broken = is_link and not target.exists()
    effective = target if not broken else path
    owner = rpm_owner(effective, rpm_command)
    if owner is None and effective != path:
        owner = rpm_owner(path, rpm_command)
    if owner:
        return None
    return {
        "name": normalized_name(path),
        "path": os.fspath(path),
        "target": os.fspath(target) if is_link else None,
        "broken_symlink": broken,
        "rpm_owner": None,
    }


def audit_paths(bin_paths: list[Path], opt_path: Path, rpm_command: str = "rpm") -> list[dict[str, object]]:
    """Audit files/links in bin paths and directories/links directly below /opt."""
    entries: list[Path] = []
    for directory in bin_paths:
        if directory.is_dir():
            entries.extend(
                path for path in directory.iterdir() if path.is_file() or path.is_symlink()
            )
    if opt_path.is_dir():
        entries.extend(
            path for path in opt_path.iterdir() if path.is_dir() or path.is_symlink()
        )
    findings = (inspect_entry(path, rpm_command) for path in sorted(set(entries)))
    return [finding for finding in findings if finding is not None]


def apply_allowlists(
    findings: list[dict[str, object]], exact: list[str], patterns: list[str]
) -> list[dict[str, object]]:
    """Suppress findings by normalized name or full path."""
    compiled = [re.compile(pattern) for pattern in patterns]
    return [
        finding
        for finding in findings
        if finding["name"] not in exact
        and finding["path"] not in exact
        and not any(
            pattern.match(str(value))
            for pattern in compiled
            for value in (finding["name"], finding["path"])
        )
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin-path", action="append", type=Path, default=[])
    parser.add_argument("--opt-path", type=Path, default=Path("/opt"))
    parser.add_argument("--rpm-command", default="rpm", help=argparse.SUPPRESS)
    args = parser.parse_args()
    bin_paths = args.bin_path or [Path("/usr/local/bin"), Path("/usr/local/sbin")]
    exact = json.loads(os.environ.get("MANUAL_INSTALL_AUDIT_ALLOWLIST", "[]"))
    patterns = json.loads(os.environ.get("MANUAL_INSTALL_AUDIT_ALLOWLIST_PATTERNS", "[]"))
    findings = audit_paths(bin_paths, args.opt_path, args.rpm_command)
    print(json.dumps(apply_allowlists(findings, exact, patterns), sort_keys=True))


if __name__ == "__main__":
    main()
