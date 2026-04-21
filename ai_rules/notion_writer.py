# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

from typing import Any

import requests

from common import request_json_with_curl_fallback, require_env_var
from schemas import DeliverableRecord, SessionPayload


NOTION_API_BASE_URL = "https://api.notion.com/v1"
NOTION_STATUS_MAP = {
    "submitted": "\u2705 Complete",
    "partial": "\U0001F4CC Follow-up Needed",
    "retry-needed": "\U0001F4CC Follow-up Needed",
    "failed": "\U0001F4CC Follow-up Needed",
}


def _build_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {require_env_var('NOTION_TOKEN')}",
        "Content-Type": "application/json",
        "Notion-Version": require_env_var("NOTION_VERSION"),
    }


def _property_rich_text(text_value: str) -> dict[str, Any]:
    return {"rich_text": [{"type": "text", "text": {"content": text_value[:2000]}}]}


def _property_title(text_value: str) -> dict[str, Any]:
    return {"title": [{"type": "text", "text": {"content": text_value[:2000]}}]}


def _property_select(option_name: str) -> dict[str, Any]:
    return {"select": {"name": option_name}}


def _property_date(start_value: str) -> dict[str, Any]:
    return {"date": {"start": start_value}}


def _text_chunks(text_value: str, chunk_size: int = 1800) -> list[str]:
    cleaned_text = text_value or ""
    return [cleaned_text[index : index + chunk_size] for index in range(0, len(cleaned_text), chunk_size)] or [""]


def _text_rich_text(text_value: str, link_url: str = "") -> list[dict[str, Any]]:
    if link_url:
        return [{"type": "text", "text": {"content": text_value[:2000], "link": {"url": link_url}}}]
    return [{"type": "text", "text": {"content": text_value[:2000]}}]


def _heading_block(text_value: str, level: str = "heading_2") -> dict[str, Any]:
    return {
        "object": "block",
        "type": level,
        level: {"rich_text": _text_rich_text(text_value)},
    }


def _paragraph_block(text_value: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": _text_rich_text(text_value)},
    }


def _paragraph_blocks(text_value: str) -> list[dict[str, Any]]:
    normalized_text = (text_value or "").strip() or "None"
    paragraph_texts = [paragraph.strip() for paragraph in normalized_text.split("\n\n") if paragraph.strip()] or ["None"]
    paragraph_blocks = []
    for paragraph_text in paragraph_texts:
        for paragraph_chunk in _text_chunks(paragraph_text):
            paragraph_blocks.append(_paragraph_block(paragraph_chunk))
    return paragraph_blocks


def _bulleted_list_item_block(text_value: str, children: list[dict[str, Any]] | None = None, link_url: str = "") -> dict[str, Any]:
    block = {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _text_rich_text(text_value, link_url=link_url)},
    }
    if children:
        block["bulleted_list_item"]["children"] = children
    return block


def _render_files_created(payload: SessionPayload) -> str:
    if not payload.deliverables:
        return "None"
    rendered_items = []
    for deliverable in payload.deliverables:
        rendered_items.append(f"{deliverable.title} ({deliverable.deliverable_type})")
    return "; ".join(rendered_items)


def _render_links(payload: SessionPayload) -> str:
    if not payload.links:
        return "None"
    return "\n".join(payload.links)


def _deliverable_children(deliverable: DeliverableRecord) -> list[dict[str, Any]]:
    detail_items = []
    if deliverable.local_path:
        detail_items.append(_bulleted_list_item_block(f"Local path: {deliverable.local_path}"))
    if deliverable.google_drive_url:
        detail_items.append(_bulleted_list_item_block("Google Drive", link_url=deliverable.google_drive_url))
    if deliverable.notion_url:
        detail_items.append(_bulleted_list_item_block("Notion", link_url=deliverable.notion_url))
    detail_items.append(_bulleted_list_item_block(f"Status: {deliverable.status}"))
    return detail_items


def _deliverable_blocks(payload: SessionPayload) -> list[dict[str, Any]]:
    if not payload.deliverables:
        return _paragraph_blocks("None")

    blocks = []
    for deliverable in payload.deliverables:
        blocks.append(
            _bulleted_list_item_block(
                f"{deliverable.title} ({deliverable.deliverable_type})",
                children=_deliverable_children(deliverable),
            )
        )
    return blocks


def _link_blocks(payload: SessionPayload) -> list[dict[str, Any]]:
    if not payload.links:
        return _paragraph_blocks("None")
    return [_bulleted_list_item_block(link_text, link_url=link_text) for link_text in payload.links]


def _routing_metadata_text(payload: SessionPayload) -> str:
    metadata_lines: list[str] = []
    if payload.delegate_role:
        metadata_lines.append(f"Delegate role: {payload.delegate_role}")
    if payload.origin_assistant_name:
        origin_surface = payload.origin_client_surface or "unknown"
        metadata_lines.append(f"Origin: {payload.origin_assistant_name} via {origin_surface}")
    if payload.origin_session_id:
        metadata_lines.append(f"Origin session ID: {payload.origin_session_id}")
    if payload.project_root:
        metadata_lines.append(f"Project root: {payload.project_root}")
    return "\n".join(metadata_lines)


def _request_json(method: str, url: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
    request_headers = _build_headers()
    try:
        response = requests.request(
            method,
            url,
            headers=request_headers,
            json=json_body,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as request_error:
        transport_error_types = (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.SSLError,
        )
        if not isinstance(request_error, transport_error_types):
            raise
        return request_json_with_curl_fallback(
            method=method,
            url=url,
            headers=request_headers,
            json_body=json_body,
            timeout_seconds=30,
        )


def _resolve_data_source_id(database_id: str, data_source_id: str) -> str:
    if data_source_id.strip():
        return data_source_id.strip()
    if not database_id.strip():
        raise RuntimeError("Missing Notion data_source_id in config.yaml")

    database_payload = _request_json("GET", f"{NOTION_API_BASE_URL}/databases/{database_id.strip()}")
    data_sources = database_payload.get("data_sources") or []
    if len(data_sources) != 1:
        raise RuntimeError(
            "Could not resolve a single Notion data_source_id from database_id. "
            "Set notion.data_source_id explicitly in config.yaml."
        )
    return data_sources[0]["id"]


def create_session_page(database_id: str, data_source_id: str, payload: SessionPayload) -> str:
    resolved_data_source_id = _resolve_data_source_id(database_id, data_source_id)

    page_title = f"{payload.ended_at[:10]} {payload.project_name} {payload.session_type}"
    page_payload = {
        "parent": {"type": "data_source_id", "data_source_id": resolved_data_source_id},
        "properties": {
            "Session Title": _property_title(page_title),
            "Session ID": _property_rich_text(payload.session_id),
            "Business": _property_select(payload.business),
            "Project Name": _property_rich_text(payload.project_name),
            "Assistant Name": _property_rich_text(payload.assistant_name),
            "Client Surface": _property_rich_text(payload.client_surface),
            "Session Type": _property_select(payload.session_type),
            "Submission Status": _property_select(payload.status),
            "Submission Stage": _property_select(payload.submission_stage),
            "Status": _property_select(NOTION_STATUS_MAP.get(payload.status, "\U0001F4CB Reference Only")),
            "Session Summary": _property_rich_text(payload.session_summary or "None"),
            "Work Completed": _property_rich_text(payload.work_completed or payload.session_summary or "None"),
            "Deliverables": _property_rich_text(_render_files_created(payload)),
            "Links": _property_rich_text(_render_links(payload)),
            "Next Steps": _property_rich_text(payload.next_steps or "None"),
            "Open Questions": _property_rich_text(payload.open_questions or "None"),
            "Started At": _property_date(payload.started_at),
            "Ended At": _property_date(payload.ended_at),
        },
    }
    response_payload = _request_json("POST", f"{NOTION_API_BASE_URL}/pages", page_payload)
    return response_payload["id"]


def _build_session_blocks(payload: SessionPayload) -> list[dict[str, Any]]:
    session_blocks: list[dict[str, Any]] = []
    session_blocks.append(_heading_block("Session Summary"))
    session_blocks.extend(_paragraph_blocks(payload.session_summary))

    session_blocks.append(_heading_block("Work Completed"))
    session_blocks.extend(_paragraph_blocks(payload.work_completed))

    routing_metadata_text = _routing_metadata_text(payload)
    if routing_metadata_text:
        session_blocks.append(_heading_block("Routing Metadata"))
        session_blocks.extend(_paragraph_blocks(routing_metadata_text))

    session_blocks.append(_heading_block("Deliverables"))
    session_blocks.extend(_deliverable_blocks(payload))

    session_blocks.append(_heading_block("Links"))
    session_blocks.extend(_link_blocks(payload))

    session_blocks.append(_heading_block("Next Steps"))
    session_blocks.extend(_paragraph_blocks(payload.next_steps))

    session_blocks.append(_heading_block("Open Questions"))
    session_blocks.extend(_paragraph_blocks(payload.open_questions))

    session_blocks.append(_heading_block("Full Transcript"))
    session_blocks.extend(_paragraph_blocks(payload.full_transcript))
    return session_blocks


def append_session_body(page_id: str, payload: SessionPayload) -> None:
    session_blocks = _build_session_blocks(payload)
    for start_index in range(0, len(session_blocks), 100):
        blocks_payload = {"children": session_blocks[start_index : start_index + 100]}
        _request_json("PATCH", f"{NOTION_API_BASE_URL}/blocks/{page_id}/children", blocks_payload)
