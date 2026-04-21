# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

from pathlib import Path

from common import ensure_directory, load_project_roots


RULE_BLOCK_NAMES = (
    "naming-standard",
    "notion-copy-paste-formatting",
    "social-campaign-output-standard",
    "session-closeout-standard",
    "blog-database-template-standard",
    "writing-natural-punctuation-standard",
    "cli-ownership-policy",
)


def load_rule_block(rule_blocks_dir: Path, rule_block_name: str) -> str:
    with (rule_blocks_dir / f"{rule_block_name}.md").open("r", encoding="utf-8") as rule_block_file:
        return rule_block_file.read().strip()


def upsert_managed_block(existing_text: str, block_name: str, replacement_text: str) -> str:
    start_marker = f"<!-- BEGIN MANAGED: {block_name} -->"
    end_marker = f"<!-- END MANAGED: {block_name} -->"
    managed_block = f"{start_marker}\n{replacement_text}\n{end_marker}"

    if start_marker in existing_text and end_marker in existing_text:
        before_start, after_start = existing_text.split(start_marker, 1)
        _, after_end = after_start.split(end_marker, 1)
        return f"{before_start}{managed_block}{after_end}"

    if existing_text.strip():
        return f"{existing_text.rstrip()}\n\n{managed_block}\n"
    return f"{managed_block}\n"


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_roots = load_project_roots().get("roots", [])
    rule_blocks_dir = script_dir / "rule_blocks"

    loaded_rule_blocks = {rule_block_name: load_rule_block(rule_blocks_dir, rule_block_name) for rule_block_name in RULE_BLOCK_NAMES}

    for configured_root in project_roots:
        root_path = Path(configured_root["path"])
        ensure_directory(root_path)
        for managed_file_name in configured_root.get("manage_files", []):
            managed_file_path = root_path / managed_file_name
            existing_text = ""
            if managed_file_path.exists():
                existing_text = managed_file_path.read_text(encoding="utf-8")

            updated_text = existing_text
            for rule_block_name, rule_block_text in loaded_rule_blocks.items():
                updated_text = upsert_managed_block(updated_text, rule_block_name, rule_block_text)

            managed_file_path.write_text(updated_text, encoding="utf-8")
            print(f"synced: {managed_file_path}")


if __name__ == "__main__":
    main()
