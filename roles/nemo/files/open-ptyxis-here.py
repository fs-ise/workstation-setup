#!/usr/bin/env python3

"""Open a new Ptyxis Bash window with a directory as its process cwd."""

from pathlib import Path
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} DIRECTORY", file=sys.stderr)
        return 2

    directory = Path(sys.argv[1]).expanduser().resolve()
    if not directory.is_dir():
        print(f"Not a directory: {directory}", file=sys.stderr)
        return 2

    subprocess.Popen(
        ["ptyxis", "--new-window", "--", "bash"],
        cwd=directory,
        start_new_session=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
