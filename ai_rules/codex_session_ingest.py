# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from inference import infer_business_from_path, infer_project_name_from_path, infer_session_type_from_text


IGNORED_USER_PREFIXES = (
    "# AGENTS.md instructions",
    "<environment_context>",
)
HOME_PATH = Path.home().resolve()
GENERIC_PATH_NAMES = {"documents", HOME_PATH.name.lower(), "users"}
URL_PATTERN = re.compile(r"https?://[^\s)>\]]+")
QUOTED_WINDOWS_PATH_PATTERN = re.compile(r"['\"]([A-Za-z]:\\[^'\"]+)['\"]")


@dataclass
class CodexSessionPayload:
    raw_payload: dict[str, Any]
    session_path: Path
    thread_name: str
    updated_at: str
    latest_event_at: str
    workdir: str


def _parse_timestamp(timestamp_text: str) -> datetime:
    return datetime.fromisoformat(timestamp_text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _format_timestamp(timestamp_value: datetime) -> str:
    return timestamp_value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json_lines(jsonl_path: Path) -> list[dict[str, Any]]:
    session_events: list[dict[str, Any]] = []
    with jsonl_path.open("r", encoding="utf-8") as session_file:
        for raw_line in session_file:
            stripped_line = raw_line.strip()
            if not stripped_line:
                continue
            session_events.append(json.loads(stripped_line))
    return session_events


def _load_session_index(session_index_path: Path) -> dict[str, dict[str, str]]:
    if not session_index_path.exists():
        return {}
    indexed_sessions: dict[str, dict[str, str]] = {}
    for session_entry in _load_json_lines(session_index_path):
        session_id = (session_entry.get("id") or "").strip()
        if session_id:
            indexed_sessions[session_id] = {
                "thread_name": (session_entry.get("thread_name") or "").strip(),
                "updated_at": (session_entry.get("updated_at") or "").strip(),
            }
    return indexed_sessions


def _extract_message_text(message_payload: dict[str, Any]) -> str:
    extracted_parts: list[str] = []
    for content_item in message_payload.get("content") or []:
        item_type = content_item.get("type")
        if item_type in {"input_text", "output_text"}:
            extracted_parts.append((content_item.get("text") or "").strip())
    return "\n\n".join(part for part in extracted_parts if part).strip()


def _is_meaningful_user_text(text_value: str) -> bool:
    stripped_text = (text_value or "").strip()
    if not stripped_text:
        return False
    return not any(stripped_text.startswith(prefix) for prefix in IGNORED_USER_PREFIXES)


def _iter_transcript_entries(session_events: list[dict[str, Any]]) -> list[tuple[str, str, str, str]]:
    transcript_entries: list[tuple[str, str, str, str]] = []
    for session_event in session_events:
        if session_event.get("type") != "response_item":
            continue
        payload = session_event.get("payload") or {}
        if payload.get("type") != "message":
            continue
        role = (payload.get("role") or "").strip()
        if role not in {"user", "assistant"}:
            continue
        message_text = _extract_message_text(payload)
        if role == "user" and not _is_meaningful_user_text(message_text):
            continue
        if not message_text:
            continue
        transcript_entries.append(
            (
                session_event.get("timestamp", ""),
                role,
                (payload.get("phase") or "").strip(),
                message_text,
            )
        )
    return transcript_entries


def _render_full_transcript(transcript_entries: list[tuple[str, str, str, str]]) -> str:
    rendered_chunks: list[str] = []
    for timestamp_text, role, phase, message_text in transcript_entries:
        role_label = role.upper()
        if phase:
            role_label = f"{role_label} {phase}"
        rendered_chunks.append(f"[{timestamp_text}] {role_label}\n{message_text}")
    return "\n\n".join(rendered_chunks).strip()


def _latest_assistant_message(transcript_entries: list[tuple[str, str, str, str]]) -> str:
    for _, role, phase, message_text in reversed(transcript_entries):
        if role == "assistant" and (phase == "final_answer" or not phase):
            return message_text
    for _, role, _, message_text in reversed(transcript_entries):
        if role == "assistant":
            return message_text
    return ""


def _first_user_message(transcript_entries: list[tuple[str, str, str, str]]) -> str:
    for _, role, _, message_text in transcript_entries:
        if role == "user":
            return message_text
    return ""


def _extract_links(*text_values: str) -> list[str]:
    unique_links: list[str] = []
    seen_links: set[str] = set()
    for text_value in text_values:
        for matched_url in URL_PATTERN.findall(text_value or ""):
            if matched_url not in seen_links:
                unique_links.append(matched_url)
                seen_links.add(matched_url)
    return unique_links


def _clean_summary_text(text_value: str, fallback_text: str) -> str:
    stripped_text = (text_value or "").strip()
    if not stripped_text:
        return fallback_text
    first_paragraph = stripped_text.split("\n\n", 1)[0].strip()
    return first_paragraph or fallback_text


def _extract_next_steps(final_text: str) -> str:
    for paragraph in (final_text or "").split("\n\n"):
        cleaned_paragraph = paragraph.strip()
        if cleaned_paragraph.lower().startswith("if you want"):
            return cleaned_paragraph
    return ""


def _extract_workdirs(session_events: list[dict[str, Any]]) -> Counter[str]:
    workdir_counter: Counter[str] = Counter()
    for session_event in session_events:
        if session_event.get("type") == "session_meta":
            session_meta = session_event.get("payload") or {}
            cwd_text = (session_meta.get("cwd") or "").strip()
            if cwd_text:
                candidate_path = Path(cwd_text).resolve()
                candidate_name = candidate_path.name.strip().lower()
                workdir_counter[cwd_text] += 1 if candidate_name in GENERIC_PATH_NAMES else 3
            continue

        if session_event.get("type") != "response_item":
            continue
        payload = session_event.get("payload") or {}
        if payload.get("type") != "function_call" or payload.get("name") != "shell_command":
            continue

        try:
            shell_args = json.loads(payload.get("arguments") or "{}")
        except json.JSONDecodeError:
            continue

        workdir_text = (shell_args.get("workdir") or "").strip()
        if workdir_text:
            candidate_path = Path(workdir_text).resolve()
            candidate_name = candidate_path.name.strip().lower()
            workdir_counter[workdir_text] += 1 if candidate_name in GENERIC_PATH_NAMES else 4

        command_text = shell_args.get("command") or ""
        for matched_path_text in QUOTED_WINDOWS_PATH_PATTERN.findall(command_text):
            candidate_path = Path(matched_path_text)
            if candidate_path.suffix:
                workdir_counter[str(candidate_path.parent.resolve())] += 5
            else:
                workdir_counter[str(candidate_path.resolve())] += 5
    return workdir_counter


def _pick_primary_workdir(session_events: list[dict[str, Any]], thread_name: str) -> Path:
    candidate_workdirs = _extract_workdirs(session_events)
    best_path = HOME_PATH / "Documents"
    best_sort_key = (-1, -1, -1, best_path.as_posix())

    for workdir_text, usage_count in candidate_workdirs.items():
        candidate_path = Path(workdir_text).resolve()
        candidate_depth = len(candidate_path.parts)
        candidate_name = candidate_path.name.strip().lower()
        is_non_generic_name = 1 if candidate_name not in GENERIC_PATH_NAMES else 0
        sort_key = (is_non_generic_name, usage_count, candidate_depth, candidate_path.as_posix().lower())
        if sort_key > best_sort_key:
            best_sort_key = sort_key
            best_path = candidate_path

    if best_path.name.strip():
        return best_path

    slug_text = re.sub(r"[^a-z0-9]+", "-", (thread_name or "").lower()).strip("-")
    if slug_text:
        return HOME_PATH / "Documents" / slug_text
    return HOME_PATH / "Documents"


def _infer_business(primary_workdir: Path, thread_name: str, first_user_message: str, default_business: str) -> str:
    inferred_business = infer_business_from_path(primary_workdir)
    if inferred_business:
        return inferred_business

    combined_text = " ".join((thread_name, first_user_message)).lower()
    for business_slug in ("mna", "tga", "tgah", "shl", "personal"):
        if re.search(rf"\b{re.escape(business_slug)}\b", combined_text):
            return business_slug
    return default_business


def _infer_project_name(primary_workdir: Path, thread_name: str) -> str:
    inferred_project_name = infer_project_name_from_path(primary_workdir)
    if inferred_project_name and inferred_project_name not in GENERIC_PATH_NAMES:
        return inferred_project_name

    slug_text = re.sub(r"[^a-z0-9]+", "-", (thread_name or "").lower()).strip("-")
    return slug_text or "codex-session"


def latest_event_timestamp(session_events: list[dict[str, Any]]) -> datetime:
    timestamps = [_parse_timestamp(session_event["timestamp"]) for session_event in session_events if session_event.get("timestamp")]
    if not timestamps:
        raise RuntimeError("Codex session file has no timestamps")
    return max(timestamps)


def is_session_stale(session_events: list[dict[str, Any]], stale_minutes: int) -> bool:
    cutoff_timestamp = datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)
    return latest_event_timestamp(session_events) <= cutoff_timestamp


def is_timestamp_stale(timestamp_text: str, stale_minutes: int) -> bool:
    cutoff_timestamp = datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)
    return _parse_timestamp(timestamp_text) <= cutoff_timestamp


def build_codex_session_payload(
    session_path: Path,
    session_index_path: Path,
    default_business: str = "personal",
) -> CodexSessionPayload:
    session_events = _load_json_lines(session_path)
    if not session_events:
        raise RuntimeError(f"Codex session file is empty: {session_path}")

    session_meta = next((event.get("payload") or {} for event in session_events if event.get("type") == "session_meta"), {})
    session_id = (session_meta.get("id") or "").strip()
    started_at_text = (session_meta.get("timestamp") or "").strip()
    if not session_id or not started_at_text:
        raise RuntimeError(f"Codex session file is missing required metadata: {session_path}")

    indexed_sessions = _load_session_index(session_index_path)
    indexed_metadata = indexed_sessions.get(session_id, {})
    thread_name = indexed_metadata.get("thread_name", "").strip()
    updated_at_text = indexed_metadata.get("updated_at", "").strip()

    transcript_entries = _iter_transcript_entries(session_events)
    first_user_message = _first_user_message(transcript_entries)
    final_assistant_message = _latest_assistant_message(transcript_entries)
    full_transcript_text = _render_full_transcript(transcript_entries)

    primary_workdir = _pick_primary_workdir(session_events, thread_name)
    business = _infer_business(primary_workdir, thread_name, first_user_message, default_business=default_business)
    project_name = _infer_project_name(primary_workdir, thread_name)
    latest_event_at = latest_event_timestamp(session_events)

    session_summary = _clean_summary_text(
        first_user_message or thread_name,
        fallback_text=f"Codex session for {project_name}.",
    )
    work_completed = _clean_summary_text(
        final_assistant_message,
        fallback_text=f"Completed Codex session for {project_name}.",
    )

    raw_payload = {
        "session_id": session_id,
        "business": business,
        "project_name": project_name,
        "assistant_name": "codex",
        "client_surface": "codex-cli",
        "session_type": infer_session_type_from_text(thread_name, first_user_message, final_assistant_message),
        "started_at": started_at_text,
        "ended_at": _format_timestamp(latest_event_at),
        "status": "submitted",
        "submission_stage": "archive",
        "session_summary": session_summary,
        "work_completed": work_completed,
        "deliverables": [],
        "links": _extract_links(first_user_message, final_assistant_message),
        "next_steps": _extract_next_steps(final_assistant_message),
        "open_questions": "",
        "full_transcript": full_transcript_text or session_summary,
    }

    return CodexSessionPayload(
        raw_payload=raw_payload,
        session_path=session_path,
        thread_name=thread_name,
        updated_at=updated_at_text,
        latest_event_at=_format_timestamp(latest_event_at),
        workdir=str(primary_workdir),
    )
