# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

import requests

from common import ensure_directory, request_json_with_curl_fallback, require_env_var, write_json
from media_ingest_models import MediaFileRecord, MediaIngestRecord


NOTION_API_BASE_URL = "https://api.notion.com/v1"
MEDIA_TYPE_OPTIONS = ("audio", "video", "image", "other", "mixed")
STATUS_OPTIONS = ("Downloaded", "Notion Failed")
DURATION_OPTIONS = ("short", "mid", "long")
COMPLEXITY_OPTIONS = ("cuts-only", "graded", "composited")
TRACK_OPTIONS = ("single", "multi")
OUTPUT_OPTIONS = ("reel", "short", "youtube", "client", "reference")
EDIT_ENVIRONMENT_OPTIONS = ("LumaFusion", "Premiere Pro", "None")
PROJECT_STATUS_OPTIONS = ("ingested", "classified", "in-edit", "exported", "published")


def _build_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {require_env_var('NOTION_TOKEN')}",
        "Content-Type": "application/json",
        "Notion-Version": require_env_var("NOTION_VERSION"),
    }


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
        if not response.content:
            return {}
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


def _property_rich_text(text_value: str) -> dict[str, Any]:
    safe_text = (text_value or "None")[:2000]
    return {"rich_text": [{"type": "text", "text": {"content": safe_text}}]}


def _property_title(text_value: str) -> dict[str, Any]:
    safe_text = (text_value or "Untitled")[:2000]
    return {"title": [{"type": "text", "text": {"content": safe_text}}]}


def _property_select(option_name: str) -> dict[str, Any]:
    return {"select": {"name": option_name}}


def _property_checkbox(value: bool) -> dict[str, Any]:
    return {"checkbox": bool(value)}


def _property_date(start_value: str) -> dict[str, Any]:
    return {"date": {"start": start_value}}


def _property_url(url_value: str) -> dict[str, Any]:
    return {"url": url_value}


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
    paragraph_blocks: list[dict[str, Any]] = []
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


def _format_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "0 B"
    suffixes = ("B", "KB", "MB", "GB", "TB")
    size_value = float(size_bytes)
    suffix_index = 0
    while size_value >= 1024 and suffix_index < len(suffixes) - 1:
        size_value /= 1024
        suffix_index += 1
    return f"{size_value:.1f} {suffixes[suffix_index]}"


def _format_duration(raw_duration: Any) -> str:
    try:
        duration_value = float(raw_duration)
    except (TypeError, ValueError):
        return "Unknown"
    if duration_value < 0:
        return "Unknown"
    return f"{duration_value:.2f}s"


def _safe_float(raw_value: Any) -> float:
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return 0.0


def _record_duration_seconds(record: MediaIngestRecord) -> float:
    durations: list[float] = []
    for file_record in record.files:
        source_duration = _safe_float(file_record.source_metadata.get("duration"))
        ffprobe_duration = _safe_float((file_record.ffprobe_payload.get("format") or {}).get("duration"))
        if source_duration > 0:
            durations.append(source_duration)
        if ffprobe_duration > 0:
            durations.append(ffprobe_duration)
    return max(durations) if durations else 0.0


def _duration_class(record: MediaIngestRecord) -> str:
    duration_seconds = _record_duration_seconds(record)
    if duration_seconds <= 90:
        return "short"
    if duration_seconds <= 600:
        return "mid"
    return "long"


def _is_vertical(record: MediaIngestRecord) -> bool:
    for file_record in record.files:
        for stream_payload in (file_record.ffprobe_payload.get("streams") or []):
            if not isinstance(stream_payload, dict):
                continue
            if stream_payload.get("codec_type") != "video":
                continue
            width = int(_safe_float(stream_payload.get("width")))
            height = int(_safe_float(stream_payload.get("height")))
            if width > 0 and height > width:
                return True
    return False


def _track_count(record: MediaIngestRecord) -> str:
    if len(record.files) > 1:
        return "multi"
    for file_record in record.files:
        video_stream_count = 0
        audio_stream_count = 0
        for stream_payload in (file_record.ffprobe_payload.get("streams") or []):
            if not isinstance(stream_payload, dict):
                continue
            if stream_payload.get("codec_type") == "video":
                video_stream_count += 1
            if stream_payload.get("codec_type") == "audio":
                audio_stream_count += 1
        if video_stream_count > 1 or audio_stream_count > 2:
            return "multi"
    return "single"


def _output_destination(record: MediaIngestRecord) -> str:
    source_url = (record.source_url or "").lower()
    duration_seconds = _record_duration_seconds(record)
    if "instagram.com" in source_url or "tiktok.com" in source_url:
        return "reel"
    if "youtube.com" in source_url or "youtu.be" in source_url:
        if duration_seconds <= 60 and _is_vertical(record):
            return "short"
        return "youtube"
    return "reference"


def _stream_summary(stream_payload: dict[str, Any]) -> str:
    codec_type = stream_payload.get("codec_type") or "unknown"
    codec_name = stream_payload.get("codec_name") or "unknown"
    if codec_type == "video":
        width = stream_payload.get("width") or "?"
        height = stream_payload.get("height") or "?"
        return f"video: {codec_name} {width}x{height}"
    if codec_type == "audio":
        sample_rate = stream_payload.get("sample_rate") or "?"
        channels = stream_payload.get("channels") or "?"
        return f"audio: {codec_name} {sample_rate}Hz {channels}ch"
    return f"{codec_type}: {codec_name}"


def _normalize_source_metadata(source_metadata: dict[str, Any]) -> list[str]:
    selected_lines: list[str] = []
    selected_fields = (
        ("id", "ID"),
        ("title", "Title"),
        ("extractor", "Extractor"),
        ("extractor_key", "Extractor Key"),
        ("uploader", "Uploader"),
        ("channel", "Channel"),
        ("upload_date", "Upload Date"),
        ("duration", "Duration"),
        ("playlist_title", "Playlist"),
        ("playlist_index", "Playlist Index"),
    )
    for field_name, label in selected_fields:
        field_value = source_metadata.get(field_name)
        if field_value not in (None, "", []):
            if field_name == "duration":
                selected_lines.append(f"{label}: {_format_duration(field_value)}")
            else:
                selected_lines.append(f"{label}: {field_value}")
    if source_metadata.get("webpage_url"):
        selected_lines.append(f"Webpage URL: {source_metadata['webpage_url']}")
    if source_metadata.get("original_url"):
        selected_lines.append(f"Original URL: {source_metadata['original_url']}")
    if source_metadata.get("description"):
        description_text = " ".join(str(source_metadata["description"]).split())
        selected_lines.append(f"Description: {description_text[:500]}")
    if source_metadata.get("tags"):
        selected_lines.append(f"Tags: {', '.join(str(tag) for tag in source_metadata['tags'][:20])}")
    if source_metadata.get("categories"):
        selected_lines.append(f"Categories: {', '.join(str(category) for category in source_metadata['categories'][:20])}")
    return selected_lines or ["None"]


def _normalize_ffprobe_payload(file_record: MediaFileRecord) -> list[str]:
    ffprobe_payload = file_record.ffprobe_payload or {}
    if ffprobe_payload.get("error"):
        return [
            f"Size: {_format_size(file_record.size_bytes)}",
            f"ffprobe error: {ffprobe_payload['error']}",
        ]
    format_payload = ffprobe_payload.get("format") or {}
    stream_payloads = ffprobe_payload.get("streams") or []

    normalized_lines = [
        f"Format: {format_payload.get('format_name') or 'Unknown'}",
        f"Duration: {_format_duration(format_payload.get('duration'))}",
        f"Bitrate: {format_payload.get('bit_rate') or 'Unknown'}",
        f"Size: {_format_size(file_record.size_bytes)}",
    ]
    for stream_payload in stream_payloads[:6]:
        normalized_lines.append(f"Stream: {_stream_summary(stream_payload)}")
    return normalized_lines


def _database_state_from_path(state_path: Path) -> dict[str, str]:
    if not state_path.exists():
        return {}
    with state_path.open("r", encoding="utf-8") as state_file:
        payload = json.load(state_file)
    return payload if isinstance(payload, dict) else {}


def _normalize_notion_id(raw_value: str, label: str) -> str:
    candidate = raw_value.strip()
    if not candidate:
        return ""
    if candidate.startswith("collection://"):
        candidate = candidate.replace("collection://", "", 1)

    matches = re.findall(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[0-9a-fA-F]{32}",
        candidate,
    )
    if matches:
        candidate = matches[-1]

    try:
        return str(uuid.UUID(candidate))
    except ValueError as value_error:
        raise RuntimeError(f"Invalid {label}: {raw_value}") from value_error


def _save_database_state(state_path: Path, database_id: str, data_source_id: str, parent_page_id: str, database_title: str) -> None:
    ensure_directory(state_path.parent)
    state_payload = _database_state_from_path(state_path)
    state_payload.update(
        {
            "database_id": database_id,
            "data_source_id": data_source_id,
            "parent_page_id": parent_page_id,
            "database_title": database_title,
        }
    )
    write_json(state_path, state_payload)


def _resolve_data_source_id(database_id: str, data_source_id: str) -> str:
    if data_source_id.strip():
        return data_source_id.strip()
    if not database_id.strip():
        raise RuntimeError("Missing Notion media database_id and data_source_id.")

    database_payload = _request_json("GET", f"{NOTION_API_BASE_URL}/databases/{database_id.strip()}")
    data_sources = database_payload.get("data_sources") or []
    if len(data_sources) != 1:
        raise RuntimeError(
            "Could not resolve a single media data_source_id from database_id. "
            "Set MEDIA_INGEST_DATA_SOURCE_ID explicitly."
        )
    return data_sources[0]["id"]


def _create_media_database(parent_page_id: str, database_title: str) -> tuple[str, str]:
    database_payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": database_title}}],
        "description": [
            {
                "type": "text",
                "text": {"content": "Media downloaded from Kali WSL and logged with yt-dlp plus ffprobe metadata."},
            }
        ],
        "initial_data_source": {
            "properties": {
                "Name": {"title": {}},
                "Date Added": {"date": {}},
                "Source URL": {"url": {}},
                "Source Key": {"rich_text": {}},
                "Local Path Tail": {"rich_text": {}},
                "Media Type": {
                    "select": {
                        "options": [{"name": media_type_option} for media_type_option in MEDIA_TYPE_OPTIONS]
                    }
                },
                "Extractor": {"select": {"options": []}},
                "Uploader": {"rich_text": {}},
                "Status": {
                    "select": {
                        "options": [{"name": status_option} for status_option in STATUS_OPTIONS]
                    }
                },
            }
        },
    }
    create_response = _request_json("POST", f"{NOTION_API_BASE_URL}/databases", database_payload)
    database_id = create_response["id"]
    data_source_id = _resolve_data_source_id(database_id, "")
    return database_id, data_source_id


def _ensure_media_data_source_schema(data_source_id: str) -> None:
    data_source_payload = _request_json("GET", f"{NOTION_API_BASE_URL}/data_sources/{data_source_id}")
    properties_payload = data_source_payload.get("properties") or {}
    patch_payload: dict[str, Any] = {"properties": {}}
    if "Source Key" not in properties_payload:
        patch_payload["properties"]["Source Key"] = {"rich_text": {}}
    if "Duration Class" not in properties_payload:
        patch_payload["properties"]["Duration Class"] = {
            "select": {"options": [{"name": option_name} for option_name in DURATION_OPTIONS]}
        }
    if "Edit Complexity" not in properties_payload:
        patch_payload["properties"]["Edit Complexity"] = {
            "select": {"options": [{"name": option_name} for option_name in COMPLEXITY_OPTIONS]}
        }
    if "Track Count" not in properties_payload:
        patch_payload["properties"]["Track Count"] = {
            "select": {"options": [{"name": option_name} for option_name in TRACK_OPTIONS]}
        }
    if "Output Destination" not in properties_payload:
        patch_payload["properties"]["Output Destination"] = {
            "select": {"options": [{"name": option_name} for option_name in OUTPUT_OPTIONS]}
        }
    if "Edit Environment" not in properties_payload:
        patch_payload["properties"]["Edit Environment"] = {
            "select": {"options": [{"name": option_name} for option_name in EDIT_ENVIRONMENT_OPTIONS]}
        }
    if "Synced to iCloud" not in properties_payload:
        patch_payload["properties"]["Synced to iCloud"] = {"checkbox": {}}
    if "Project Status" not in properties_payload:
        patch_payload["properties"]["Project Status"] = {
            "select": {"options": [{"name": option_name} for option_name in PROJECT_STATUS_OPTIONS]}
        }
    if "Routing Note" not in properties_payload:
        patch_payload["properties"]["Routing Note"] = {"rich_text": {}}
    if patch_payload["properties"]:
        _request_json("PATCH", f"{NOTION_API_BASE_URL}/data_sources/{data_source_id}", patch_payload)


def ensure_media_database(
    parent_page_id: str,
    state_path: Path,
    database_id: str = "",
    data_source_id: str = "",
    database_title: str = "Media Library",
) -> tuple[str, str]:
    saved_state = _database_state_from_path(state_path)
    resolved_database_id = _normalize_notion_id(
        database_id.strip() or str(saved_state.get("database_id", "")).strip(),
        "MEDIA_INGEST_DATABASE_ID",
    )
    resolved_data_source_id = _normalize_notion_id(
        data_source_id.strip() or str(saved_state.get("data_source_id", "")).strip(),
        "MEDIA_INGEST_DATA_SOURCE_ID",
    )
    resolved_parent_page_id = _normalize_notion_id(
        parent_page_id.strip() or str(saved_state.get("parent_page_id", "")).strip(),
        "MEDIA_INGEST_PARENT_PAGE_ID",
    )

    if resolved_database_id:
        resolved_data_source_id = _resolve_data_source_id(resolved_database_id, resolved_data_source_id)
        _ensure_media_data_source_schema(resolved_data_source_id)
        _save_database_state(
            state_path=state_path,
            database_id=resolved_database_id,
            data_source_id=resolved_data_source_id,
            parent_page_id=resolved_parent_page_id,
            database_title=database_title,
        )
        return resolved_database_id, resolved_data_source_id

    if not resolved_parent_page_id:
        raise RuntimeError(
            "Missing MEDIA_INGEST_PARENT_PAGE_ID. Set it before the first run so the media database can be created."
        )

    resolved_database_id, resolved_data_source_id = _create_media_database(
        parent_page_id=resolved_parent_page_id,
        database_title=database_title,
    )
    _ensure_media_data_source_schema(resolved_data_source_id)
    _save_database_state(
        state_path=state_path,
        database_id=resolved_database_id,
        data_source_id=resolved_data_source_id,
        parent_page_id=resolved_parent_page_id,
        database_title=database_title,
    )
    return resolved_database_id, resolved_data_source_id


def create_media_page(data_source_id: str, record: MediaIngestRecord, source_key: str) -> str:
    page_payload = {
        "parent": {"type": "data_source_id", "data_source_id": data_source_id},
        "properties": {
            "Name": _property_title(record.title),
            "Date Added": _property_date(record.completed_at),
            "Source URL": _property_url(record.source_url),
            "Source Key": _property_rich_text(source_key),
            "Local Path Tail": _property_rich_text(record.local_path_tail),
            "Media Type": _property_select(record.media_type),
            "Extractor": _property_select(record.extractor or "Unknown"),
            "Uploader": _property_rich_text(record.uploader or "Unknown"),
            "Status": _property_select(record.status or "Downloaded"),
            "Duration Class": _property_select(_duration_class(record)),
            "Edit Complexity": _property_select("cuts-only"),
            "Track Count": _property_select(_track_count(record)),
            "Output Destination": _property_select(_output_destination(record)),
            "Synced to iCloud": _property_checkbox(False),
            "Project Status": _property_select("ingested"),
            "Routing Note": _property_rich_text(""),
        },
    }
    response_payload = _request_json("POST", f"{NOTION_API_BASE_URL}/pages", page_payload)
    return response_payload["id"]


def query_media_pages(data_source_id: str) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    next_cursor = ""
    while True:
        query_payload: dict[str, Any] = {"page_size": 100}
        if next_cursor:
            query_payload["start_cursor"] = next_cursor
        response_payload = _request_json("POST", f"{NOTION_API_BASE_URL}/data_sources/{data_source_id}/query", query_payload)
        pages.extend(response_payload.get("results") or [])
        if not response_payload.get("has_more"):
            break
        next_cursor = str(response_payload.get("next_cursor") or "").strip()
        if not next_cursor:
            break
    return pages


def _files_created_blocks(record: MediaIngestRecord) -> list[dict[str, Any]]:
    if not record.files:
        return _paragraph_blocks("None")

    blocks: list[dict[str, Any]] = []
    for file_record in record.files:
        children = [
            _bulleted_list_item_block(f"Media type: {file_record.media_type}"),
            _bulleted_list_item_block(f"Local path tail: {file_record.local_path_tail}"),
            _bulleted_list_item_block(f"Size: {_format_size(file_record.size_bytes)}"),
        ]
        blocks.append(
            _bulleted_list_item_block(
                f"{file_record.file_name} ({file_record.media_type}, {_format_size(file_record.size_bytes)})",
                children=children,
            )
        )
    return blocks


def _source_metadata_blocks(record: MediaIngestRecord) -> list[dict[str, Any]]:
    if not record.files:
        return _paragraph_blocks("None")

    blocks: list[dict[str, Any]] = []
    for file_record in record.files:
        normalized_lines = _normalize_source_metadata(file_record.source_metadata)
        child_blocks = []
        for normalized_line in normalized_lines:
            if normalized_line.startswith("Webpage URL: "):
                link_url = normalized_line.replace("Webpage URL: ", "", 1)
                child_blocks.append(_bulleted_list_item_block("Webpage URL", link_url=link_url))
            elif normalized_line.startswith("Original URL: "):
                link_url = normalized_line.replace("Original URL: ", "", 1)
                child_blocks.append(_bulleted_list_item_block("Original URL", link_url=link_url))
            else:
                child_blocks.append(_bulleted_list_item_block(normalized_line))
        blocks.append(_bulleted_list_item_block(file_record.file_name, children=child_blocks))
    return blocks


def _media_metadata_blocks(record: MediaIngestRecord) -> list[dict[str, Any]]:
    if not record.files:
        return _paragraph_blocks("None")

    blocks: list[dict[str, Any]] = []
    for file_record in record.files:
        child_blocks = [_bulleted_list_item_block(normalized_line) for normalized_line in _normalize_ffprobe_payload(file_record)]
        blocks.append(_bulleted_list_item_block(file_record.file_name, children=child_blocks))
    return blocks


def _raw_metadata_snapshot_text(record: MediaIngestRecord) -> str:
    compact_snapshot = {
        "source_url": record.source_url,
        "submitted_at": record.submitted_at,
        "completed_at": record.completed_at,
        "media_type": record.media_type,
        "extractor": record.extractor,
        "uploader": record.uploader,
        "files": [
            {
                "file_name": file_record.file_name,
                "media_type": file_record.media_type,
                "local_path_tail": file_record.local_path_tail,
                "source_metadata": file_record.source_metadata,
                "ffprobe_payload": file_record.ffprobe_payload,
            }
            for file_record in record.files
        ],
    }
    return json.dumps(compact_snapshot, indent=2, ensure_ascii=True)


def _build_media_blocks(record: MediaIngestRecord) -> list[dict[str, Any]]:
    media_blocks: list[dict[str, Any]] = []

    media_blocks.append(_heading_block("Summary"))
    media_blocks.extend(
        _paragraph_blocks(
            "\n".join(
                [
                    f"Submitted URL: {record.source_url}",
                    f"Submitted At: {record.submitted_at}",
                    f"Completed At: {record.completed_at}",
                    f"Extractor: {record.extractor or 'Unknown'}",
                    f"Uploader: {record.uploader or 'Unknown'}",
                    f"Media Type: {record.media_type}",
                    f"Files Downloaded: {len(record.files)}",
                ]
            )
        )
    )

    media_blocks.append(_heading_block("Files Created"))
    media_blocks.extend(_files_created_blocks(record))

    media_blocks.append(_heading_block("Source Metadata"))
    media_blocks.extend(_source_metadata_blocks(record))

    media_blocks.append(_heading_block("Media Metadata"))
    media_blocks.extend(_media_metadata_blocks(record))

    media_blocks.append(_heading_block("Raw Metadata Snapshot"))
    media_blocks.extend(_paragraph_blocks(_raw_metadata_snapshot_text(record)))

    return media_blocks


def append_media_body(page_id: str, record: MediaIngestRecord) -> None:
    media_blocks = _build_media_blocks(record)
    for start_index in range(0, len(media_blocks), 100):
        blocks_payload = {"children": media_blocks[start_index : start_index + 100]}
        _request_json("PATCH", f"{NOTION_API_BASE_URL}/blocks/{page_id}/children", blocks_payload)
