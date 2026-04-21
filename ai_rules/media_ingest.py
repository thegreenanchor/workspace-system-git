# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from urllib.parse import urldefrag
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import ensure_directory, write_json
from media_ingest_config import MediaIngestConfig, load_media_ingest_config
from media_ingest_models import MediaFileRecord, MediaIngestRecord
from media_notion_writer import append_media_body, create_media_page, ensure_media_database


AUDIO_EXTENSIONS = {
    ".aac",
    ".aiff",
    ".alac",
    ".flac",
    ".m4a",
    ".mka",
    ".mp3",
    ".ogg",
    ".opus",
    ".wav",
    ".wma",
}
VIDEO_EXTENSIONS = {
    ".3gp",
    ".avi",
    ".flv",
    ".m2ts",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".ogv",
    ".ts",
    ".webm",
    ".wmv",
}
IMAGE_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".gif",
    ".heic",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".tiff",
    ".webp",
}
SIDE_CAR_SUFFIXES = (".description", ".info.json", ".part", ".ytdl")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download media with yt-dlp from Kali WSL and log it to Notion.")
    parser.add_argument("url", help="Source URL supported by yt-dlp")
    parser.add_argument("--audio-only", action="store_true", help="Extract audio and convert it to MP3.")
    parser.add_argument("--dry-run", action="store_true", help="Skip Notion writes and print the computed record JSON.")
    parser.add_argument(
        "--cookies-from-browser",
        default="",
        help="Pass through to yt-dlp, for example `firefox` or `firefox:profile`.",
    )
    return parser.parse_args()


def _require_wsl_runtime() -> None:
    if os.name == "nt":
        raise RuntimeError("This script is intended to run from Kali in WSL, not native Windows.")


def _require_binary(binary_name: str) -> None:
    if shutil.which(binary_name):
        return
    raise RuntimeError(f"Required binary not found in PATH: {binary_name}")


def _prepare_library_root(media_library_root: Path) -> None:
    ensure_directory(media_library_root)
    for bucket_name in ("audio", "video", "image", "other", ".incoming"):
        ensure_directory(media_library_root / bucket_name)


def _run_subprocess(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode == 0:
        return result

    command_text = " ".join(command)
    stderr_text = (result.stderr or "").strip()
    stdout_text = (result.stdout or "").strip()
    raise RuntimeError(f"Command failed: {command_text}\nstderr: {stderr_text}\nstdout: {stdout_text}")


def _build_yt_dlp_command(config: MediaIngestConfig, staging_dir: Path, source_url: str, audio_only: bool) -> list[str]:
    command = [
        config.yt_dlp_binary,
        "--windows-filenames",
        "--write-info-json",
        "--no-progress",
        "--newline",
        "-P",
        str(staging_dir),
        "-o",
        "%(title).180B [%(id)s].%(ext)s",
    ]
    if config.yt_dlp_cookies_from_browser:
        command.extend(["--cookies-from-browser", config.yt_dlp_cookies_from_browser])
    if audio_only:
        command.extend(["-f", "bestaudio/best", "-x", "--audio-format", "mp3"])
    else:
        command.extend(["-f", "bestvideo*+bestaudio/best"])
    command.append(source_url)
    return command


def _is_sidecar_file(file_path: Path) -> bool:
    return any(str(file_path).endswith(sidecar_suffix) for sidecar_suffix in SIDE_CAR_SUFFIXES)


def _load_info_payloads(staging_dir: Path) -> dict[str, dict[str, Any]]:
    info_payloads: dict[str, dict[str, Any]] = {}
    for info_path in sorted(staging_dir.rglob("*.info.json")):
        with info_path.open("r", encoding="utf-8") as info_file:
            info_payload = json.load(info_file)
        base_name = info_path.name[: -len(".info.json")]
        info_payloads[base_name] = info_payload
    return info_payloads


def _collect_downloaded_media_files(staging_dir: Path) -> list[Path]:
    media_files: list[Path] = []
    for file_path in sorted(staging_dir.rglob("*")):
        if not file_path.is_file():
            continue
        if _is_sidecar_file(file_path):
            continue
        media_files.append(file_path)
    if not media_files:
        raise RuntimeError("yt-dlp completed without producing any downloadable media files.")
    return media_files


def _classify_media_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in AUDIO_EXTENSIONS:
        return "audio"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    return "other"


def _unique_destination_path(destination_dir: Path, file_name: str) -> Path:
    candidate_path = destination_dir / file_name
    if not candidate_path.exists():
        return candidate_path

    stem = candidate_path.stem
    suffix = candidate_path.suffix
    for candidate_index in range(2, 10000):
        candidate_path = destination_dir / f"{stem} ({candidate_index}){suffix}"
        if not candidate_path.exists():
            return candidate_path
    raise RuntimeError(f"Could not allocate a unique destination path for {file_name}")


def _run_ffprobe(ffprobe_binary: str, file_path: Path) -> dict[str, Any]:
    command = [
        ffprobe_binary,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]
    try:
        result = _run_subprocess(command)
    except RuntimeError as ffprobe_error:
        return {"error": str(ffprobe_error)}
    return _compact_ffprobe_payload(json.loads(result.stdout or "{}"))


def _compact_ffprobe_payload(ffprobe_payload: dict[str, Any]) -> dict[str, Any]:
    if ffprobe_payload.get("error"):
        return ffprobe_payload

    format_payload = ffprobe_payload.get("format") or {}
    stream_payloads = ffprobe_payload.get("streams") or []

    compact_format = {}
    for field_name in ("format_name", "format_long_name", "duration", "size", "bit_rate", "probe_score"):
        field_value = format_payload.get(field_name)
        if field_value not in (None, "", []):
            compact_format[field_name] = field_value
    if format_payload.get("tags"):
        compact_format["tags"] = {
            tag_name: tag_value
            for tag_name, tag_value in format_payload["tags"].items()
            if tag_name in {"major_brand", "minor_version", "compatible_brands", "encoder"}
        }

    compact_streams = []
    for stream_payload in stream_payloads[:6]:
        compact_stream = {}
        for field_name in (
            "index",
            "codec_name",
            "codec_long_name",
            "profile",
            "codec_type",
            "width",
            "height",
            "pix_fmt",
            "sample_rate",
            "channels",
            "channel_layout",
            "r_frame_rate",
            "avg_frame_rate",
            "duration",
            "bit_rate",
        ):
            field_value = stream_payload.get(field_name)
            if field_value not in (None, "", []):
                compact_stream[field_name] = field_value
        if stream_payload.get("tags"):
            compact_stream["tags"] = {
                tag_name: tag_value
                for tag_name, tag_value in stream_payload["tags"].items()
                if tag_name in {"language", "handler_name", "vendor_id"}
            }
        compact_streams.append(compact_stream)

    return {"format": compact_format, "streams": compact_streams}


def _relative_tail(media_library_root: Path, file_path: Path) -> str:
    return str(file_path.relative_to(media_library_root)).replace("\\", "/")


def _resolve_source_metadata(file_path: Path, info_payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    file_stem = file_path.stem
    if file_stem in info_payloads:
        return info_payloads[file_stem]

    fallback_name = file_path.name
    for base_name, info_payload in info_payloads.items():
        if fallback_name.startswith(base_name):
            return info_payload
    return {}


def _compact_source_metadata(source_metadata: dict[str, Any]) -> dict[str, Any]:
    if not source_metadata:
        return {}

    compact_payload: dict[str, Any] = {}
    selected_fields = (
        "id",
        "title",
        "fulltitle",
        "display_id",
        "extractor",
        "extractor_key",
        "webpage_url",
        "original_url",
        "uploader",
        "uploader_id",
        "uploader_url",
        "channel",
        "channel_id",
        "channel_url",
        "upload_date",
        "timestamp",
        "duration",
        "duration_string",
        "view_count",
        "like_count",
        "comment_count",
        "categories",
        "tags",
        "description",
        "media_type",
        "availability",
        "live_status",
        "playlist_title",
        "playlist_index",
        "thumbnail",
        "ext",
        "format",
        "format_id",
        "resolution",
        "width",
        "height",
        "fps",
        "vcodec",
        "acodec",
        "abr",
        "asr",
        "audio_channels",
    )
    for field_name in selected_fields:
        field_value = source_metadata.get(field_name)
        if field_value in (None, "", []):
            continue
        if field_name == "description":
            compact_payload[field_name] = " ".join(str(field_value).split())[:500]
        elif field_name == "tags":
            compact_payload[field_name] = [str(tag) for tag in field_value[:20]]
        else:
            compact_payload[field_name] = field_value
    return compact_payload


def _normalize_submitted_url(source_url: str) -> str:
    normalized_url, _ = urldefrag(source_url.strip())
    return normalized_url


def _probe_source_identity(config: MediaIngestConfig, source_url: str) -> str:
    command = [
        config.yt_dlp_binary,
        "--skip-download",
        "--print",
        "%(extractor)s\t%(id)s\t%(webpage_url)s",
    ]
    if config.yt_dlp_cookies_from_browser:
        command.extend(["--cookies-from-browser", config.yt_dlp_cookies_from_browser])
    command.append(source_url)
    result = _run_subprocess(command)
    output_lines = [output_line.strip() for output_line in (result.stdout or "").splitlines() if output_line.strip()]
    if len(output_lines) != 1:
        return f"url:{_normalize_submitted_url(source_url)}"

    extractor_value, media_id, webpage_url = (output_lines[0].split("\t") + ["", "", ""])[:3]
    extractor_value = extractor_value.strip()
    media_id = media_id.strip()
    webpage_url = webpage_url.strip()
    if extractor_value and media_id:
        return f"{extractor_value}:{media_id}"
    if webpage_url:
        return f"url:{_normalize_submitted_url(webpage_url)}"
    return f"url:{_normalize_submitted_url(source_url)}"


def _load_media_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {}
    with state_path.open("r", encoding="utf-8") as state_file:
        payload = json.load(state_file)
    return payload if isinstance(payload, dict) else {}


def _save_media_ingest_state(
    state_path: Path,
    source_key: str,
    record: MediaIngestRecord,
    page_id: str,
) -> None:
    state_payload = _load_media_state(state_path)
    ingests_payload = state_payload.get("ingests")
    if not isinstance(ingests_payload, dict):
        ingests_payload = {}
    ingests_payload[source_key] = {
        "page_id": page_id,
        "record": asdict(record),
        "updated_at": record.completed_at,
    }
    state_payload["ingests"] = ingests_payload
    write_json(state_path, state_payload)


def _existing_ingest_entry(state_path: Path, source_key: str) -> dict[str, Any]:
    state_payload = _load_media_state(state_path)
    ingests_payload = state_payload.get("ingests")
    if not isinstance(ingests_payload, dict):
        return {}
    entry_payload = ingests_payload.get(source_key)
    return entry_payload if isinstance(entry_payload, dict) else {}


def _files_exist_for_entry(entry_payload: dict[str, Any]) -> bool:
    record_payload = entry_payload.get("record")
    if not isinstance(record_payload, dict):
        return False
    files_payload = record_payload.get("files")
    if not isinstance(files_payload, list) or not files_payload:
        return False
    for file_payload in files_payload:
        if not isinstance(file_payload, dict):
            return False
        final_path = str(file_payload.get("final_path", "")).strip()
        if not final_path or not Path(final_path).exists():
            return False
    return True


def _move_downloaded_files(
    media_library_root: Path,
    media_files: list[Path],
    info_payloads: dict[str, dict[str, Any]],
    ffprobe_binary: str,
) -> list[MediaFileRecord]:
    records: list[MediaFileRecord] = []
    for media_file in media_files:
        media_type = _classify_media_type(media_file)
        destination_dir = media_library_root / media_type
        ensure_directory(destination_dir)
        destination_path = _unique_destination_path(destination_dir, media_file.name)
        shutil.move(str(media_file), str(destination_path))
        file_size_bytes = destination_path.stat().st_size
        ffprobe_payload = _run_ffprobe(ffprobe_binary, destination_path)
        source_metadata = _compact_source_metadata(_resolve_source_metadata(media_file, info_payloads))
        records.append(
            MediaFileRecord(
                file_name=destination_path.name,
                media_type=media_type,
                final_path=str(destination_path),
                local_path_tail=_relative_tail(media_library_root, destination_path),
                size_bytes=file_size_bytes,
                ffprobe_payload=ffprobe_payload,
                source_metadata=source_metadata,
            )
        )
    return records


def _collect_media_type(file_records: list[MediaFileRecord]) -> str:
    media_types = sorted({file_record.media_type for file_record in file_records})
    if not media_types:
        return "other"
    if len(media_types) == 1:
        return media_types[0]
    return "mixed"


def _first_non_empty(file_records: list[MediaFileRecord], field_name: str) -> str:
    for file_record in file_records:
        metadata_value = str(file_record.source_metadata.get(field_name, "")).strip()
        if metadata_value:
            return metadata_value
    return ""


def _build_page_title(file_records: list[MediaFileRecord]) -> str:
    if not file_records:
        return "Untitled"
    if len(file_records) == 1:
        return file_records[0].file_name
    return f"{file_records[0].file_name} (+{len(file_records) - 1} more)"


def _build_local_path_tail(file_records: list[MediaFileRecord]) -> str:
    if not file_records:
        return "None"
    if len(file_records) == 1:
        return file_records[0].local_path_tail
    return f"{file_records[0].local_path_tail} (+{len(file_records) - 1} more)"


def _download_media(config: MediaIngestConfig, source_url: str, audio_only: bool) -> list[MediaFileRecord]:
    incoming_root = config.media_library_root / ".incoming"
    with tempfile.TemporaryDirectory(dir=str(incoming_root), prefix="media-ingest-") as staging_dir_raw:
        staging_dir = Path(staging_dir_raw)
        yt_dlp_command = _build_yt_dlp_command(config, staging_dir, source_url, audio_only)
        _run_subprocess(yt_dlp_command)

        info_payloads = _load_info_payloads(staging_dir)
        media_files = _collect_downloaded_media_files(staging_dir)
        return _move_downloaded_files(
            media_library_root=config.media_library_root,
            media_files=media_files,
            info_payloads=info_payloads,
            ffprobe_binary=config.ffprobe_binary,
        )


def _build_ingest_record(source_url: str, submitted_at: str, completed_at: str, file_records: list[MediaFileRecord]) -> MediaIngestRecord:
    return MediaIngestRecord(
        source_url=source_url,
        submitted_at=submitted_at,
        completed_at=completed_at,
        title=_build_page_title(file_records),
        local_path_tail=_build_local_path_tail(file_records),
        media_type=_collect_media_type(file_records),
        extractor=_first_non_empty(file_records, "extractor") or _first_non_empty(file_records, "extractor_key"),
        uploader=_first_non_empty(file_records, "uploader") or _first_non_empty(file_records, "channel"),
        status="Downloaded",
        files=file_records,
    )


def _cleanup_dry_run_files(file_records: list[MediaFileRecord]) -> str:
    cleanup_errors: list[str] = []
    for file_record in file_records:
        final_path = Path(file_record.final_path)
        if not final_path.exists():
            continue
        try:
            final_path.unlink()
        except OSError as cleanup_error:
            cleanup_errors.append(f"{final_path}: {cleanup_error}")
    return "; ".join(cleanup_errors)


def main() -> None:
    args = parse_args()
    try:
        _require_wsl_runtime()

        config = load_media_ingest_config()
        if args.cookies_from_browser.strip():
            config.yt_dlp_cookies_from_browser = args.cookies_from_browser.strip()
        _require_binary(config.yt_dlp_binary)
        _require_binary(config.ffprobe_binary)
        _require_binary(config.ffmpeg_binary)

        _prepare_library_root(config.media_library_root)
        source_key = _probe_source_identity(config=config, source_url=args.url)

        database_id = ""
        data_source_id = ""
        if not args.dry_run:
            database_id, data_source_id = ensure_media_database(
                parent_page_id=config.parent_page_id,
                state_path=config.state_path,
                database_id=config.database_id,
                data_source_id=config.data_source_id,
                database_title=config.database_title,
            )
            existing_entry = _existing_ingest_entry(config.state_path, source_key)
            if existing_entry and existing_entry.get("page_id") and _files_exist_for_entry(existing_entry):
                output_payload = {
                    "record": existing_entry.get("record"),
                    "database_id": database_id,
                    "data_source_id": data_source_id,
                    "page_id": existing_entry.get("page_id", ""),
                    "dry_run": args.dry_run,
                    "notion_error": "",
                    "cleanup_error": "",
                    "source_key": source_key,
                    "deduped": True,
                }
                print(json.dumps(output_payload, indent=2, ensure_ascii=True))
                raise SystemExit(0)

        submitted_at = datetime.now(timezone.utc).isoformat()
        file_records = _download_media(config=config, source_url=args.url, audio_only=args.audio_only)
        completed_at = datetime.now(timezone.utc).isoformat()
        ingest_record = _build_ingest_record(
            source_url=args.url,
            submitted_at=submitted_at,
            completed_at=completed_at,
            file_records=file_records,
        )

        output_payload: dict[str, Any] = {
            "record": asdict(ingest_record),
            "database_id": database_id,
            "data_source_id": data_source_id,
            "page_id": "",
            "dry_run": args.dry_run,
            "notion_error": "",
            "cleanup_error": "",
            "source_key": source_key,
            "deduped": False,
        }

        if args.dry_run:
            output_payload["cleanup_error"] = _cleanup_dry_run_files(file_records)

        if not args.dry_run:
            try:
                page_id = create_media_page(data_source_id=data_source_id, record=ingest_record, source_key=source_key)
                append_media_body(page_id=page_id, record=ingest_record)
                _save_media_ingest_state(
                    state_path=config.state_path,
                    source_key=source_key,
                    record=ingest_record,
                    page_id=page_id,
                )
                output_payload.update(
                    {
                        "database_id": database_id,
                        "data_source_id": data_source_id,
                        "page_id": page_id,
                    }
                )
            except Exception as notion_error:
                ingest_record.status = "Notion Failed"
                output_payload.update(
                    {
                        "record": asdict(ingest_record),
                        "notion_error": str(notion_error),
                    }
                )
                print(json.dumps(output_payload, indent=2, ensure_ascii=True))
                raise SystemExit(1)

        print(json.dumps(output_payload, indent=2, ensure_ascii=True))
    except Exception as runtime_error:
        error_payload = {
            "record": None,
            "database_id": "",
            "data_source_id": "",
            "page_id": "",
            "dry_run": args.dry_run,
            "notion_error": "",
            "cleanup_error": "",
            "source_key": "",
            "deduped": False,
            "runtime_error": str(runtime_error),
        }
        print(json.dumps(error_payload, indent=2, ensure_ascii=True))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
