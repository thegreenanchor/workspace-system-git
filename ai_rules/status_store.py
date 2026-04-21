# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from common import init_status_db
from schemas import SessionPayload


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_session_record(
    sqlite_path: Path,
    payload: SessionPayload,
    raw_payload_path: Path,
    normalized_payload_path: Path,
    notion_page_id: str = "",
    google_doc_id: str = "",
    last_error: str = "",
) -> None:
    database_connection = init_status_db(sqlite_path)
    now_text = _utc_now_iso()
    database_connection.execute(
        """
        INSERT INTO sessions (
            session_id, business, project_name, assistant_name, client_surface, session_type,
            origin_assistant_name, origin_client_surface, origin_session_id, delegate_role, project_root,
            status, submission_stage, raw_payload_path, normalized_payload_path, notion_page_id,
            google_doc_id, last_error, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            business=excluded.business,
            project_name=excluded.project_name,
            assistant_name=excluded.assistant_name,
            client_surface=excluded.client_surface,
            session_type=excluded.session_type,
            origin_assistant_name=excluded.origin_assistant_name,
            origin_client_surface=excluded.origin_client_surface,
            origin_session_id=excluded.origin_session_id,
            delegate_role=excluded.delegate_role,
            project_root=excluded.project_root,
            status=excluded.status,
            submission_stage=excluded.submission_stage,
            raw_payload_path=excluded.raw_payload_path,
            normalized_payload_path=excluded.normalized_payload_path,
            notion_page_id=excluded.notion_page_id,
            google_doc_id=excluded.google_doc_id,
            last_error=excluded.last_error,
            updated_at=excluded.updated_at
        """,
        (
            payload.session_id,
            payload.business,
            payload.project_name,
            payload.assistant_name,
            payload.client_surface,
            payload.session_type,
            payload.origin_assistant_name,
            payload.origin_client_surface,
            payload.origin_session_id,
            payload.delegate_role,
            payload.project_root,
            payload.status,
            payload.submission_stage,
            str(raw_payload_path),
            str(normalized_payload_path),
            notion_page_id,
            google_doc_id,
            last_error,
            now_text,
            now_text,
        ),
    )
    database_connection.execute("DELETE FROM deliverables WHERE session_id = ?", (payload.session_id,))
    for deliverable in payload.deliverables:
        database_connection.execute(
            """
            INSERT INTO deliverables (
                session_id, title, deliverable_type, local_path, google_drive_url, notion_url, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.session_id,
                deliverable.title,
                deliverable.deliverable_type,
                deliverable.local_path,
                deliverable.google_drive_url,
                deliverable.notion_url,
                deliverable.status,
            ),
        )
    database_connection.commit()
    database_connection.close()


def record_attempt(sqlite_path: Path, payload: SessionPayload, error_message: str = "") -> None:
    database_connection = init_status_db(sqlite_path)
    existing_attempts = database_connection.execute(
        "SELECT COUNT(*) FROM attempts WHERE session_id = ?",
        (payload.session_id,),
    ).fetchone()[0]
    database_connection.execute(
        """
        INSERT INTO attempts (session_id, attempt_number, status, submission_stage, error_message, attempted_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload.session_id,
            existing_attempts + 1,
            payload.status,
            payload.submission_stage,
            error_message,
            _utc_now_iso(),
        ),
    )
    database_connection.commit()
    database_connection.close()


def get_session_record(sqlite_path: Path, session_id: str) -> sqlite3.Row | None:
    database_connection = init_status_db(sqlite_path)
    database_connection.row_factory = sqlite3.Row
    row = database_connection.execute(
        "SELECT * FROM sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    database_connection.close()
    return row


def get_retry_candidates(sqlite_path: Path, target_status: str | None = None) -> list[sqlite3.Row]:
    database_connection = init_status_db(sqlite_path)
    database_connection.row_factory = sqlite3.Row
    if target_status:
        rows = database_connection.execute(
            "SELECT * FROM sessions WHERE status = ? ORDER BY updated_at ASC",
            (target_status,),
        ).fetchall()
    else:
        rows = database_connection.execute(
            "SELECT * FROM sessions WHERE status IN ('partial', 'failed', 'retry-needed') ORDER BY updated_at ASC"
        ).fetchall()
    database_connection.close()
    return rows
