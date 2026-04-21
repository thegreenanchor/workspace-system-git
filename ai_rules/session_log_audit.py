# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cli_broker import get_broker_paths
from codex_session_ingest import build_codex_session_payload
from status_store import get_retry_candidates, get_session_record


def _parse_timestamp(timestamp_text: str) -> datetime:
    return datetime.fromisoformat(timestamp_text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _iter_session_files(codex_sessions_root: Path) -> list[Path]:
    return sorted(codex_sessions_root.rglob("rollout-*.jsonl"))


def _load_state(state_path: Path) -> dict[str, str]:
    if not state_path.exists():
        return {}
    with state_path.open("r", encoding="utf-8") as state_file:
        return json.load(state_file)


def _recent_cutoff(hours: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def _broker_result_payloads(result_dir: Path, recent_hours: int) -> list[dict[str, Any]]:
    cutoff = _recent_cutoff(recent_hours)
    payloads: list[dict[str, Any]] = []
    for result_path in sorted(result_dir.glob("*.json")):
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        completed_at = (payload.get("completed_at") or payload.get("started_at") or payload.get("created_at") or "").strip()
        if not completed_at:
            continue
        if _parse_timestamp(completed_at) < cutoff:
            continue
        payloads.append(payload)
    return payloads


def audit_session_logs(runtime_config: dict[str, Any]) -> dict[str, Any]:
    automation_config = runtime_config.get("automation", {})
    recent_hours = int(automation_config.get("audit_recent_hours", 72))
    stale_minutes = int(automation_config.get("stale_minutes", 10))
    install_state = _load_state(Path(automation_config.get("state_path", "")))
    install_cutoff_text = (install_state.get("install_cutoff") or "").strip()
    install_cutoff = _parse_timestamp(install_cutoff_text) if install_cutoff_text else None

    codex_sessions_root = Path(automation_config["codex_sessions_root"]).resolve()
    codex_session_index_path = Path(automation_config["codex_session_index_path"]).resolve()
    default_business = (automation_config.get("default_business") or "personal").strip().lower()
    sqlite_path = Path(runtime_config["sqlite"]["path"]).resolve()
    broker_paths = get_broker_paths(runtime_config)
    recent_cutoff = _recent_cutoff(recent_hours)

    missing_codex_sessions: list[dict[str, str]] = []
    for session_path in _iter_session_files(codex_sessions_root):
        codex_session = build_codex_session_payload(
            session_path=session_path,
            session_index_path=codex_session_index_path,
            default_business=default_business,
        )
        latest_event_at = _parse_timestamp(codex_session.latest_event_at)
        if latest_event_at < recent_cutoff:
            continue
        if install_cutoff and latest_event_at < install_cutoff:
            continue
        if latest_event_at > datetime.now(timezone.utc) - timedelta(minutes=stale_minutes):
            continue

        session_record = get_session_record(sqlite_path, codex_session.raw_payload["session_id"])
        if session_record and session_record["status"] == "submitted":
            continue
        missing_codex_sessions.append(
            {
                "session_id": codex_session.raw_payload["session_id"],
                "latest_event_at": codex_session.latest_event_at,
                "workdir": codex_session.workdir,
                "session_path": str(session_path),
                "status": session_record["status"] if session_record else "missing",
            }
        )

    retry_candidates = [
        {
            "session_id": row["session_id"],
            "status": row["status"],
            "submission_stage": row["submission_stage"],
            "updated_at": row["updated_at"],
        }
        for row in get_retry_candidates(sqlite_path)
        if _parse_timestamp(row["updated_at"]) >= recent_cutoff
    ]

    broker_logging_gaps: list[dict[str, str]] = []
    for payload in _broker_result_payloads(broker_paths.done_dir, recent_hours):
        logging_status = (payload.get("logging_status") or "").strip().lower()
        payload_file = (payload.get("payload_file") or "").strip()
        status = (payload.get("status") or "").strip().lower()
        if not payload_file and status == "completed":
            continue
        if logging_status == "submitted":
            continue
        broker_logging_gaps.append(
            {
                "task_id": str(payload.get("task_id") or ""),
                "provider_id": str(payload.get("provider_id") or ""),
                "status": str(payload.get("status") or ""),
                "logging_status": logging_status or "missing",
            }
        )

    broker_failed_logs: list[dict[str, str]] = []
    for payload in _broker_result_payloads(broker_paths.failed_dir, recent_hours):
        provider_id = str(payload.get("provider_id") or "").strip()
        status = str(payload.get("status") or "").strip()
        if not provider_id and not status:
            continue
        task_id = str(payload.get("task_id") or "").strip()
        if task_id and get_session_record(sqlite_path, task_id):
            continue
        broker_failed_logs.append(
            {
                "task_id": task_id,
                "provider_id": provider_id,
                "status": status,
                "error_text": str(payload.get("error_text") or "")[:300],
            }
        )

    return {
        "recent_hours": recent_hours,
        "missing_codex_sessions": missing_codex_sessions,
        "retry_candidates": retry_candidates,
        "broker_logging_gaps": broker_logging_gaps,
        "broker_failed_logs": broker_failed_logs,
    }
