#!/usr/bin/env python3
"""Validate personal directory environment variables without changing the system."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


VARIABLES_FILE = Path(__file__).with_name("directory_variables.json")
STRICT_ENV = "DIRECTORY_AUDIT_STRICT"


def required_variables() -> list[dict[str, str]]:
    """Load the shared, declarative directory variable contract."""
    return json.loads(VARIABLES_FILE.read_text(encoding="utf-8"))


def audit_directories(environment: dict[str, str] | os._Environ[str] | None = None):
    """Return one (name, displayed value, error) record per required variable."""
    environment = os.environ if environment is None else environment
    results = []
    for entry in required_variables():
        name = entry["name"]
        value = environment.get(name, "")
        error = None
        if not value:
            error = "Not defined" if name not in environment else "Empty value"
        else:
            path = Path(value)
            if not path.is_absolute():
                error = "Path is not absolute"
            elif not path.is_dir():
                error = "Directory does not exist"
            else:
                try:
                    # os.access uses the real UID by default. This preserves the
                    # invoking user's permissions even if a caller has elevated
                    # effective privileges (for example through sudo/Ansible).
                    if not os.access(path, os.R_OK | os.W_OK | os.X_OK):
                        error = "Directory is not accessible by the target user"
                except OSError:
                    error = "Directory is not accessible by the target user"
        results.append((name, value, error))
    return results


def strict_validation(environment: dict[str, str] | os._Environ[str] | None = None) -> bool:
    environment = os.environ if environment is None else environment
    return environment.get(STRICT_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    results = audit_directories()
    print("Directory configuration audit")
    for name, value, error in results:
        if error:
            print(f"✗ {name:<18} {error}" + (f": {value}" if value else ""))
        else:
            print(f"✓ {name:<18} {value}")
    valid = sum(error is None for _, _, error in results)
    invalid = len(results) - valid
    print(f"\n{valid} valid, {invalid} invalid")
    if invalid and not strict_validation():
        print(f"WARNING: directory settings are report-only; set {STRICT_ENV}=true in the personal overlay to fail on invalid values.")
    return 1 if invalid and strict_validation() else 0


if __name__ == "__main__":
    sys.exit(main())
