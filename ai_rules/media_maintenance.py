# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from media_ingest import _files_exist_for_entry, _load_media_state, _probe_source_identity
from media_ingest_config import load_media_ingest_config
from media_notion_writer import query_media_pages


MEDIA_BUCKETS = ("audio", "video", "image", "other")
FILE_NAME_ID_PATTERN = re.compile(r"^(?P<prefix>.+ \[(?P<source_id>[^\]]+)\])(?: \((?P<copy>\d+)\))?(?P<ext>\.[^.]+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect and optionally clean duplicate media ingests from Kali WSL.")
    parser.add_argument("--apply", action="store_true", help="Delete duplicate local files instead of reporting only.")
    parser.add_argument(
        "--check-notion",
        action="store_true",
        help="Query the Notion media database and report duplicate pages for the same source key.",
    )
    return parser.parse_args()


def _require_wsl_runtime() -> None:
    if os.name == "nt":
        raise RuntimeError("This script is intended to run from Kali in WSL, not native Windows.")


def _parse_file_identity(file_path: Path) -> dict[str, Any]:
    match = FILE_NAME_ID_PATTERN.match(file_path.name)
    if not match:
        return {}
    source_id = match.group("source_id")
    copy_suffix = int(match.group("copy") or "0")
    canonical_base = f"{match.group('prefix')}{match.group('ext')}"
    return {
        "source_id": source_id,
        "copy_suffix": copy_suffix,
        "canonical_base": canonical_base,
        "extension": match.group("ext").lower(),
    }


def _scan_local_files(media_library_root: Path) -> list[Path]:
    media_files: list[Path] = []
    for bucket_name in MEDIA_BUCKETS:
        bucket_path = media_library_root / bucket_name
        if not bucket_path.exists():
            continue
        for file_path in sorted(bucket_path.iterdir()):
            if file_path.is_file():
                media_files.append(file_path)
    return media_files


def _build_state_indexes(state_payload: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    ingests_payload = state_payload.get("ingests")
    if not isinstance(ingests_payload, dict):
        return {}, {}

    source_id_to_key: dict[str, str] = {}
    final_path_to_key: dict[str, str] = {}
    for source_key, entry_payload in ingests_payload.items():
        if not isinstance(entry_payload, dict):
            continue
        if ":" in source_key:
            _, source_id = source_key.split(":", 1)
            source_id_to_key[source_id] = source_key
        record_payload = entry_payload.get("record")
        if not isinstance(record_payload, dict):
            continue
        files_payload = record_payload.get("files")
        if not isinstance(files_payload, list):
            continue
        for file_payload in files_payload:
            if not isinstance(file_payload, dict):
                continue
            final_path = str(file_payload.get("final_path", "")).strip()
            if final_path:
                final_path_to_key[final_path] = source_key
    return source_id_to_key, final_path_to_key


def _group_duplicate_files(media_library_root: Path, state_payload: dict[str, Any]) -> list[dict[str, Any]]:
    source_id_to_key, final_path_to_key = _build_state_indexes(state_payload)
    grouped_files: dict[str, list[dict[str, Any]]] = {}

    for file_path in _scan_local_files(media_library_root):
        identity_payload = _parse_file_identity(file_path)
        if not identity_payload:
            continue
        source_key = final_path_to_key.get(str(file_path)) or source_id_to_key.get(identity_payload["source_id"]) or f"unknown:{identity_payload['source_id']}"
        group_key = f"{source_key}|{file_path.parent.name}|{identity_payload['extension']}"
        grouped_files.setdefault(group_key, []).append(
            {
                "path": str(file_path),
                "name": file_path.name,
                "source_key": source_key,
                "source_id": identity_payload["source_id"],
                "copy_suffix": identity_payload["copy_suffix"],
                "bucket": file_path.parent.name,
            }
        )

    duplicate_groups: list[dict[str, Any]] = []
    ingests_payload = state_payload.get("ingests") if isinstance(state_payload.get("ingests"), dict) else {}
    for group_key, file_entries in grouped_files.items():
        if len(file_entries) <= 1:
            continue
        file_entries.sort(key=lambda file_entry: file_entry["copy_suffix"])
        source_key = file_entries[0]["source_key"]
        state_entry = ingests_payload.get(source_key, {}) if isinstance(ingests_payload, dict) else {}
        state_keep_path = ""
        if isinstance(state_entry, dict):
            record_payload = state_entry.get("record")
            if isinstance(record_payload, dict):
                files_payload = record_payload.get("files")
                if isinstance(files_payload, list) and files_payload:
                    state_keep_path = str(files_payload[0].get("final_path", "")).strip()

        keep_entry = None
        if state_keep_path:
            keep_entry = next((file_entry for file_entry in file_entries if file_entry["path"] == state_keep_path), None)
        if not keep_entry:
            keep_entry = next((file_entry for file_entry in file_entries if file_entry["copy_suffix"] == 0), None)
        if not keep_entry:
            keep_entry = file_entries[0]

        delete_entries = [file_entry for file_entry in file_entries if file_entry["path"] != keep_entry["path"]]
        duplicate_groups.append(
            {
                "source_key": source_key,
                "source_id": keep_entry["source_id"],
                "bucket": keep_entry["bucket"],
                "keep_path": keep_entry["path"],
                "delete_paths": [file_entry["path"] for file_entry in delete_entries],
                "all_paths": [file_entry["path"] for file_entry in file_entries],
            }
        )

    duplicate_groups.sort(key=lambda group: (group["source_key"], group["bucket"]))
    return duplicate_groups


def _delete_duplicate_files(duplicate_groups: list[dict[str, Any]]) -> list[str]:
    deletion_errors: list[str] = []
    for duplicate_group in duplicate_groups:
        for delete_path in duplicate_group["delete_paths"]:
            try:
                Path(delete_path).unlink(missing_ok=True)
            except OSError as deletion_error:
                deletion_errors.append(f"{delete_path}: {deletion_error}")
    return deletion_errors


def _property_plain_text(page_payload: dict[str, Any], property_name: str) -> str:
    properties_payload = page_payload.get("properties") or {}
    property_payload = properties_payload.get(property_name) or {}
    if "title" in property_payload:
        return "".join(item.get("plain_text", "") for item in property_payload["title"]).strip()
    if "rich_text" in property_payload:
        return "".join(item.get("plain_text", "") for item in property_payload["rich_text"]).strip()
    if "url" in property_payload:
        return str(property_payload.get("url") or "").strip()
    return ""


def _find_duplicate_notion_pages(config, state_payload: dict[str, Any]) -> list[dict[str, Any]]:
    state_database_id = str(state_payload.get("database_id", "")).strip()
    state_data_source_id = str(state_payload.get("data_source_id", "")).strip()
    data_source_id = config.data_source_id or state_data_source_id
    database_id = config.database_id or state_database_id
    if not data_source_id or not database_id:
        return []

    grouped_pages: dict[str, list[dict[str, Any]]] = {}
    for page_payload in query_media_pages(data_source_id):
        source_key = _property_plain_text(page_payload, "Source Key")
        if not source_key:
            source_url = _property_plain_text(page_payload, "Source URL")
            if source_url:
                try:
                    source_key = _probe_source_identity(config=config, source_url=source_url)
                except Exception:
                    source_key = f"url:{source_url}"
        if not source_key:
            continue
        grouped_pages.setdefault(source_key, []).append(
            {
                "page_id": page_payload.get("id", ""),
                "title": _property_plain_text(page_payload, "Name"),
                "source_url": _property_plain_text(page_payload, "Source URL"),
                "local_path_tail": _property_plain_text(page_payload, "Local Path Tail"),
            }
        )

    duplicate_pages = []
    for source_key, page_entries in grouped_pages.items():
        if len(page_entries) <= 1:
            continue
        duplicate_pages.append(
            {
                "source_key": source_key,
                "page_ids": [page_entry["page_id"] for page_entry in page_entries],
                "pages": page_entries,
            }
        )
    duplicate_pages.sort(key=lambda group: group["source_key"])
    return duplicate_pages


def main() -> None:
    args = parse_args()
    _require_wsl_runtime()

    config = load_media_ingest_config()
    state_payload = _load_media_state(config.state_path)
    duplicate_groups = _group_duplicate_files(config.media_library_root, state_payload)
    deletion_errors: list[str] = []
    if args.apply:
        deletion_errors = _delete_duplicate_files(duplicate_groups)

    duplicate_notion_pages = _find_duplicate_notion_pages(config, state_payload) if args.check_notion else []

    output_payload = {
        "media_library_root": str(config.media_library_root),
        "apply": args.apply,
        "local_duplicate_groups": duplicate_groups,
        "deleted_file_count": sum(len(group["delete_paths"]) for group in duplicate_groups) if args.apply else 0,
        "deletion_errors": deletion_errors,
        "checked_notion": args.check_notion,
        "duplicate_notion_pages": duplicate_notion_pages,
    }
    print(json.dumps(output_payload, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
