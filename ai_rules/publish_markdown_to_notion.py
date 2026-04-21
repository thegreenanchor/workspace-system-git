# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import requests

from common import load_runtime_config, request_json_with_curl_fallback, require_env_var


NOTION_API_BASE_URL = "https://api.notion.com/v1"
DEFAULT_PARENT_PAGE_ID = "3376f335-ffee-81f7-a390-d379ef2f1203"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a markdown file as a Notion page.")
    parser.add_argument("--markdown-file", required=True, help="Path to the source markdown file.")
    parser.add_argument("--title", required=True, help="Title for the Notion page.")
    parser.add_argument(
        "--parent-page-id",
        default=DEFAULT_PARENT_PAGE_ID,
        help="Parent Notion page ID. Defaults to the AI Broker Ops page.",
    )
    return parser.parse_args()


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


def _text_chunks(text_value: str, chunk_size: int = 1800) -> list[str]:
    cleaned_text = text_value or ""
    return [cleaned_text[index : index + chunk_size] for index in range(0, len(cleaned_text), chunk_size)] or [""]


def _rich_text(text_value: str) -> list[dict[str, Any]]:
    return [{"type": "text", "text": {"content": text_value[:2000]}}]


def _heading_block(text_value: str, level: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": level,
        level: {"rich_text": _rich_text(text_value)},
    }


def _paragraph_block(text_value: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": _rich_text(text_value)},
    }


def _bulleted_list_item_block(text_value: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _rich_text(text_value)},
    }


def _numbered_list_item_block(text_value: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": _rich_text(text_value)},
    }


def _code_block(text_value: str, language: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "code",
        "code": {
            "language": language if language else "plain text",
            "rich_text": _rich_text(text_value),
        },
    }


def _flush_paragraph(buffer: list[str], blocks: list[dict[str, Any]]) -> None:
    if not buffer:
        return
    paragraph_text = " ".join(part.strip() for part in buffer if part.strip()).strip()
    buffer.clear()
    if not paragraph_text:
        return
    for paragraph_chunk in _text_chunks(paragraph_text):
        blocks.append(_paragraph_block(paragraph_chunk))


def markdown_to_blocks(markdown_text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    paragraph_buffer: list[str] = []
    in_code_block = False
    code_language = "plain text"
    code_lines: list[str] = []

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code_block:
                code_text = "\n".join(code_lines).rstrip()
                if not code_text:
                    code_text = " "
                for code_chunk in _text_chunks(code_text):
                    blocks.append(_code_block(code_chunk, code_language))
                in_code_block = False
                code_language = "plain text"
                code_lines = []
            else:
                _flush_paragraph(paragraph_buffer, blocks)
                in_code_block = True
                code_language = line[3:].strip() or "plain text"
            continue

        if in_code_block:
            code_lines.append(raw_line)
            continue

        stripped = line.strip()
        if not stripped:
            _flush_paragraph(paragraph_buffer, blocks)
            continue

        if stripped.startswith("# "):
            _flush_paragraph(paragraph_buffer, blocks)
            blocks.append(_heading_block(stripped[2:].strip(), "heading_1"))
            continue
        if stripped.startswith("## "):
            _flush_paragraph(paragraph_buffer, blocks)
            blocks.append(_heading_block(stripped[3:].strip(), "heading_2"))
            continue
        if stripped.startswith("### "):
            _flush_paragraph(paragraph_buffer, blocks)
            blocks.append(_heading_block(stripped[4:].strip(), "heading_3"))
            continue
        if stripped.startswith("- "):
            _flush_paragraph(paragraph_buffer, blocks)
            bullet_text = stripped[2:].strip()
            for bullet_chunk in _text_chunks(bullet_text):
                blocks.append(_bulleted_list_item_block(bullet_chunk))
            continue
        numbered_prefix, separator, numbered_text = stripped.partition(". ")
        if separator and numbered_prefix.isdigit():
            _flush_paragraph(paragraph_buffer, blocks)
            for item_chunk in _text_chunks(numbered_text.strip()):
                blocks.append(_numbered_list_item_block(item_chunk))
            continue

        paragraph_buffer.append(stripped)

    _flush_paragraph(paragraph_buffer, blocks)
    return blocks


def create_page(parent_page_id: str, title: str) -> str:
    page_payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "properties": {
            "title": {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title[:2000]},
                    }
                ]
            }
        },
    }
    response_payload = _request_json("POST", f"{NOTION_API_BASE_URL}/pages", page_payload)
    return str(response_payload["id"])


def append_blocks(page_id: str, blocks: list[dict[str, Any]]) -> None:
    for start_index in range(0, len(blocks), 100):
        payload = {"children": blocks[start_index : start_index + 100]}
        _request_json("PATCH", f"{NOTION_API_BASE_URL}/blocks/{page_id}/children", payload)


def main() -> None:
    args = parse_args()
    load_runtime_config()
    markdown_path = Path(args.markdown_file).resolve()
    markdown_text = markdown_path.read_text(encoding="utf-8")
    blocks = markdown_to_blocks(markdown_text)
    page_id = create_page(args.parent_page_id, args.title)
    append_blocks(page_id, blocks)
    result = {
        "page_id": page_id,
        "url": f"https://www.notion.so/{page_id.replace('-', '')}",
        "title": args.title,
        "source_markdown_file": str(markdown_path),
        "parent_page_id": args.parent_page_id,
        "blocks_appended": len(blocks),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
