#!/usr/bin/env python3
"""Recursively strip the "ID" property from every item (and nested sockets)
found under any "Equipped" or "MercenaryEquipped" key, in every .json file
under the given root (default: current directory).

Usage:
    python strip_equipped_ids.py [root_dir]
"""
import json
import os
import sys
 
TARGET_KEYS = {"Equipped", "MercenaryEquipped"}


def strip_ids(node):
    """Remove "ID" from every dict nested anywhere inside node."""
    if isinstance(node, dict):
        node.pop("ID", None)
        for value in node.values():
            strip_ids(value)
    elif isinstance(node, list):
        for item in node:
            strip_ids(item)


def process_value(node):
    """Walk the whole JSON tree, applying strip_ids only under target keys."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in TARGET_KEYS:
                strip_ids(value)
            else:
                process_value(value)
    elif isinstance(node, list):
        for item in node:
            process_value(item)


def process_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"SKIP (invalid JSON): {path} -> {e}")
        return False

    process_value(data)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return True


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    changed = 0
    total = 0
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.lower().endswith(".json"):
                path = os.path.join(dirpath, name)
                total += 1
                if process_file(path):
                    changed += 1
    print(f"Processed {total} JSON files, updated {changed}.")


if __name__ == "__main__":
    main()
