# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MediaFileRecord:
    file_name: str
    media_type: str
    final_path: str
    local_path_tail: str
    size_bytes: int
    ffprobe_payload: dict[str, Any] = field(default_factory=dict)
    source_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MediaIngestRecord:
    source_url: str
    submitted_at: str
    completed_at: str
    title: str
    local_path_tail: str
    media_type: str
    extractor: str
    uploader: str
    status: str
    files: list[MediaFileRecord] = field(default_factory=list)
