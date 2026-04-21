# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive import archive_session_payloads
from common import load_runtime_config
from google_docs_writer import append_to_google_doc
from normalization import load_raw_payload, normalize_payload
from notion_writer import append_session_body, create_session_page
from status_store import get_session_record, record_attempt, upsert_session_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Submit one AI session payload.")
    parser.add_argument("--payload-file", required=True, help="Path to a JSON payload file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runtime_config = load_runtime_config()
    payload_path = Path(args.payload_file).resolve()
    raw_payload = load_raw_payload(payload_path)
    normalized_payload = normalize_payload(raw_payload)

    archive_config = runtime_config["archive"]
    archive_root = Path(archive_config["root_dir"])
    archive_backup_roots = [
        Path(backup_root)
        for backup_root in archive_config.get("backup_root_dirs", []) or []
        if str(backup_root).strip()
    ]
    sqlite_path = Path(runtime_config["sqlite"]["path"])
    notion_database_id = runtime_config["notion"]["database_id"].strip()
    notion_data_source_id = runtime_config["notion"].get("data_source_id", "").strip()
    google_doc_id = runtime_config["google_docs"]["business_docs"].get(normalized_payload.business, "").strip()

    raw_output_path, normalized_output_path = archive_session_payloads(
        archive_root=archive_root,
        raw_payload=raw_payload,
        normalized_payload=normalized_payload,
        backup_roots=archive_backup_roots,
        raw_dir_name=archive_config.get("raw_dir_name", "_raw"),
        normalized_dir_name=archive_config.get("normalized_dir_name", "_normalized"),
    )

    existing_record = get_session_record(sqlite_path, normalized_payload.session_id)
    notion_page_id = ""
    last_error = ""
    try:
        if existing_record and existing_record["status"] == "partial" and existing_record["notion_page_id"]:
            notion_page_id = existing_record["notion_page_id"]
        else:
            normalized_payload.submission_stage = "notion"
            record_attempt(sqlite_path, normalized_payload)
            notion_page_id = create_session_page(notion_database_id, notion_data_source_id, normalized_payload)
            append_session_body(notion_page_id, normalized_payload)

        normalized_payload.submission_stage = "google-doc"
        record_attempt(sqlite_path, normalized_payload)
        append_to_google_doc(google_doc_id, normalized_payload)

        normalized_payload.status = "submitted"
        normalized_payload.submission_stage = "complete"
        record_attempt(sqlite_path, normalized_payload)
    except Exception as submission_exception:
        last_error = str(submission_exception)
        if notion_page_id:
            normalized_payload.status = "partial"
            normalized_payload.submission_stage = "google-doc"
        else:
            normalized_payload.status = "retry-needed"
            normalized_payload.submission_stage = "notion"
        record_attempt(sqlite_path, normalized_payload, error_message=last_error)
        raise
    finally:
        upsert_session_record(
            sqlite_path=sqlite_path,
            payload=normalized_payload,
            raw_payload_path=raw_output_path,
            normalized_payload_path=normalized_output_path,
            notion_page_id=notion_page_id,
            google_doc_id=google_doc_id,
            last_error=last_error,
        )
        print(json.dumps({"session_id": normalized_payload.session_id, "status": normalized_payload.status}, indent=2))


if __name__ == "__main__":
    main()
