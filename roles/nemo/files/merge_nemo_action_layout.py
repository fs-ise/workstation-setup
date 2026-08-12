#!/usr/bin/python3
"""Merge one Ansible-managed action into Nemo's action layout."""

import argparse
import json
import os
import tempfile
from pathlib import Path


def merge_layout(layout, action_id, accelerator):
    """Return a layout with one managed action and no shortcut conflict."""
    managed = None

    def merge_list(items):
        nonlocal managed
        result = []
        for item in items:
            if isinstance(item, dict) and item.get("id") == action_id:
                if managed is None:
                    managed = item
                    result.append(item)
                continue
            merge_node(item)
            if isinstance(item, dict) and item.get("accelerator") == accelerator:
                del item["accelerator"]
            result.append(item)
        return result

    def merge_node(node):
        if isinstance(node, dict):
            for key, value in list(node.items()):
                if isinstance(value, list):
                    node[key] = merge_list(value)
                elif isinstance(value, dict):
                    merge_node(value)

    merge_node(layout)
    if managed is None:
        managed = {"id": action_id, "type": "action"}
        if isinstance(layout, list):
            layout.append(managed)
        elif isinstance(layout, dict):
            layout.setdefault("toplevel", []).append(managed)
        else:
            raise ValueError("Nemo action layout must be a JSON object or array")
    managed["accelerator"] = accelerator
    return layout


def update_file(path, action_id, accelerator):
    """Update path atomically and return whether its effective content changed."""
    path = Path(path)
    if path.exists():
        original = json.loads(path.read_text(encoding="utf-8"))
    else:
        original = {"toplevel": []}
    merged = merge_layout(json.loads(json.dumps(original)), action_id, accelerator)
    if merged == original:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as output:
        json.dump(merged, output, indent=4, ensure_ascii=False)
        output.write("\n")
        temporary_path = output.name
    os.replace(temporary_path, path)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("layout")
    parser.add_argument("action_id")
    parser.add_argument("accelerator")
    args = parser.parse_args()
    print("changed" if update_file(args.layout, args.action_id, args.accelerator) else "unchanged")


if __name__ == "__main__":
    main()
