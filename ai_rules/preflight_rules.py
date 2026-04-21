# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import argparse
from pathlib import Path

from common import load_project_roots, load_runtime_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report the governing root and standards coverage for a working directory.")
    parser.add_argument("--cwd", default=str(Path.cwd()), help="Working directory to inspect")
    return parser.parse_args()


def find_governing_root(current_path: Path, configured_roots: list[dict]) -> dict | None:
    current_text = str(current_path.resolve()).replace("/", "\\").lower()
    matching_roots = []
    for configured_root in configured_roots:
        root_path = configured_root["path"].replace("/", "\\").lower()
        if current_text.startswith(root_path):
            matching_roots.append((len(root_path), configured_root))
    if not matching_roots:
        return None
    matching_roots.sort(key=lambda matching_root: matching_root[0], reverse=True)
    return matching_roots[0][1]


def main() -> None:
    args = parse_args()
    current_path = Path(args.cwd).resolve()
    project_roots = load_project_roots().get("roots", [])
    runtime_config = load_runtime_config()

    governing_root = find_governing_root(current_path, project_roots)
    if not governing_root:
        print(f"No governing root found for: {current_path}")
        return

    print(f"cwd: {current_path}")
    print(f"governing_root: {governing_root['path']}")
    print(f"business: {governing_root.get('business', '')}")
    print(f"managed_files: {', '.join(governing_root.get('manage_files', []))}")
    print(f"standards_root: {runtime_config['standards']['root_dir']}")


if __name__ == "__main__":
    main()
