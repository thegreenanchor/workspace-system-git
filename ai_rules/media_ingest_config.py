# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from common import ensure_directory


DEFAULT_MEDIA_LIBRARY_ROOT = Path(__file__).resolve().parents[1] / "raw-media-downloads"
DEFAULT_MEDIA_CONFIG_DIR = Path.home() / ".config" / "ai-rules-media-ingest"
DEFAULT_MEDIA_ENV_PATH = DEFAULT_MEDIA_CONFIG_DIR / ".env"
DEFAULT_MEDIA_STATE_PATH = DEFAULT_MEDIA_CONFIG_DIR / "state.json"


@dataclass
class MediaIngestConfig:
    media_library_root: Path
    parent_page_id: str
    database_id: str
    data_source_id: str
    database_title: str
    state_path: Path
    yt_dlp_binary: str
    ffprobe_binary: str
    ffmpeg_binary: str
    yt_dlp_cookies_from_browser: str


def _expand_path(raw_path: str) -> Path:
    return Path(raw_path).expanduser()


def load_media_ingest_config() -> MediaIngestConfig:
    env_path = _expand_path(os.getenv("MEDIA_INGEST_ENV_FILE", str(DEFAULT_MEDIA_ENV_PATH)))
    if env_path.exists():
        load_dotenv(env_path, override=False, encoding="utf-8-sig")

    state_path = _expand_path(os.getenv("MEDIA_INGEST_STATE_PATH", str(DEFAULT_MEDIA_STATE_PATH)))
    ensure_directory(state_path.parent)

    media_library_root = _expand_path(os.getenv("MEDIA_LIBRARY_ROOT", str(DEFAULT_MEDIA_LIBRARY_ROOT)))

    return MediaIngestConfig(
        media_library_root=media_library_root,
        parent_page_id=os.getenv("MEDIA_INGEST_PARENT_PAGE_ID", "").strip(),
        database_id=os.getenv("MEDIA_INGEST_DATABASE_ID", "").strip(),
        data_source_id=os.getenv("MEDIA_INGEST_DATA_SOURCE_ID", "").strip(),
        database_title=os.getenv("MEDIA_INGEST_DATABASE_TITLE", "Media Library").strip() or "Media Library",
        state_path=state_path,
        yt_dlp_binary=os.getenv("YT_DLP_BIN", "yt-dlp").strip() or "yt-dlp",
        ffprobe_binary=os.getenv("FFPROBE_BIN", "ffprobe").strip() or "ffprobe",
        ffmpeg_binary=os.getenv("FFMPEG_BIN", "ffmpeg").strip() or "ffmpeg",
        yt_dlp_cookies_from_browser=os.getenv("YT_DLP_COOKIES_FROM_BROWSER", "").strip(),
    )
