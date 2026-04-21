# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from schemas import (
    BUSINESS_VALUES,
    SESSION_TYPE_VALUES,
    STATUS_VALUES,
    SUBMISSION_STAGE_VALUES,
    DeliverableRecord,
    SessionPayload,
)


def _require_non_empty(field_name: str, field_value: str) -> str:
    cleaned_value = (field_value or "").strip()
    if not cleaned_value:
        raise ValueError(f"Missing required field: {field_name}")
    return cleaned_value


def _validate_url_format(field_name: str, field_value: str) -> str:
    if not field_value:
        return ""
    parsed_url = urlparse(field_value)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError(f"Invalid URL format for {field_name}: {field_value}")
    return field_value


def _validate_local_path(deliverable_path: str) -> str:
    if not deliverable_path:
        return ""
    resolved_path = Path(deliverable_path)
    if not resolved_path.exists():
        raise ValueError(f"Deliverable local_path does not exist: {deliverable_path}")
    return str(resolved_path)


def _normalize_optional_text(raw_value: str, lowercase: bool = False) -> str:
    cleaned_value = (raw_value or "").strip()
    return cleaned_value.lower() if lowercase else cleaned_value


def _normalize_project_root(project_root: str) -> str:
    normalized_root = _normalize_optional_text(project_root)
    if not normalized_root:
        return ""
    return str(Path(normalized_root).resolve())


def _coerce_deliverables(raw_deliverables: list[dict]) -> list[DeliverableRecord]:
    normalized_deliverables: list[DeliverableRecord] = []
    for raw_deliverable in raw_deliverables or []:
        deliverable_title = _require_non_empty("deliverable.title", raw_deliverable.get("title", ""))
        deliverable_type = _require_non_empty("deliverable.deliverable_type", raw_deliverable.get("deliverable_type", ""))
        normalized_deliverables.append(
            DeliverableRecord(
                title=deliverable_title,
                deliverable_type=deliverable_type,
                local_path=_validate_local_path(raw_deliverable.get("local_path", "")),
                google_drive_url=_validate_url_format("deliverable.google_drive_url", raw_deliverable.get("google_drive_url", "")),
                notion_url=_validate_url_format("deliverable.notion_url", raw_deliverable.get("notion_url", "")),
                status=(raw_deliverable.get("status") or "submitted").strip() or "submitted",
            )
        )
    return normalized_deliverables


def load_raw_payload(payload_path: Path) -> dict:
    with payload_path.open("r", encoding="utf-8") as payload_file:
        return json.load(payload_file)


def normalize_payload(raw_payload: dict) -> SessionPayload:
    session_id = (raw_payload.get("session_id") or str(uuid.uuid4())).strip()
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", session_id):
        raise ValueError("session_id must be a UUID string")

    business = _require_non_empty("business", raw_payload.get("business", "")).lower()
    if business not in BUSINESS_VALUES:
        raise ValueError(f"business must be one of: {', '.join(sorted(BUSINESS_VALUES))}")

    project_name = _require_non_empty("project_name", raw_payload.get("project_name", "")).lower()
    assistant_name = _require_non_empty("assistant_name", raw_payload.get("assistant_name", "")).lower()
    client_surface = _require_non_empty("client_surface", raw_payload.get("client_surface", "")).lower()

    session_type = _require_non_empty("session_type", raw_payload.get("session_type", "")).lower()
    if session_type not in SESSION_TYPE_VALUES:
        raise ValueError(f"session_type must be one of: {', '.join(sorted(SESSION_TYPE_VALUES))}")

    status = _require_non_empty("status", raw_payload.get("status", "")).lower()
    if status not in STATUS_VALUES:
        raise ValueError(f"status must be one of: {', '.join(sorted(STATUS_VALUES))}")

    submission_stage = _require_non_empty("submission_stage", raw_payload.get("submission_stage", "")).lower()
    if submission_stage not in SUBMISSION_STAGE_VALUES:
        raise ValueError(f"submission_stage must be one of: {', '.join(sorted(SUBMISSION_STAGE_VALUES))}")

    started_at = _require_non_empty("started_at", raw_payload.get("started_at", ""))
    ended_at = _require_non_empty("ended_at", raw_payload.get("ended_at", ""))

    session_summary = (raw_payload.get("session_summary") or "").strip()
    work_completed = (raw_payload.get("work_completed") or "").strip()
    next_steps = (raw_payload.get("next_steps") or "").strip()
    open_questions = (raw_payload.get("open_questions") or "").strip()
    full_transcript = _require_non_empty("full_transcript", raw_payload.get("full_transcript", ""))
    origin_assistant_name = _normalize_optional_text(raw_payload.get("origin_assistant_name", ""), lowercase=True)
    origin_client_surface = _normalize_optional_text(raw_payload.get("origin_client_surface", ""), lowercase=True)
    origin_session_id = _normalize_optional_text(raw_payload.get("origin_session_id", ""))
    delegate_role = _normalize_optional_text(raw_payload.get("delegate_role", ""), lowercase=True)
    project_root = _normalize_project_root(raw_payload.get("project_root", ""))

    if not any([session_summary, work_completed, next_steps, open_questions, full_transcript]):
        raise ValueError("At least one content section must be non-empty")

    links = [_validate_url_format("links[]", raw_link) for raw_link in (raw_payload.get("links") or []) if raw_link]
    deliverables = _coerce_deliverables(raw_payload.get("deliverables") or [])

    return SessionPayload(
        session_id=session_id,
        business=business,
        project_name=project_name,
        assistant_name=assistant_name,
        client_surface=client_surface,
        session_type=session_type,
        started_at=started_at,
        ended_at=ended_at,
        status=status,
        submission_stage=submission_stage,
        session_summary=session_summary,
        work_completed=work_completed,
        deliverables=deliverables,
        links=links,
        next_steps=next_steps,
        open_questions=open_questions,
        full_transcript=full_transcript,
        origin_assistant_name=origin_assistant_name,
        origin_client_surface=origin_client_surface,
        origin_session_id=origin_session_id,
        delegate_role=delegate_role,
        project_root=project_root,
    )


def render_timestamp_for_filename(timestamp_text: str) -> str:
    parsed_timestamp = datetime.fromisoformat(timestamp_text.replace("Z", "+00:00"))
    return parsed_timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d_%H%M%S")


def payload_as_dict(payload: SessionPayload) -> dict:
    return asdict(payload)
