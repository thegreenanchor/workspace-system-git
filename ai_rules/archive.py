# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

from pathlib import Path
import sys
from typing import Iterable

from common import ensure_directory, write_json
from normalization import payload_as_dict, render_timestamp_for_filename
from schemas import SessionPayload


def build_archive_paths(
    archive_root: Path,
    payload: SessionPayload,
    raw_dir_name: str = "_raw",
    normalized_dir_name: str = "_normalized",
) -> tuple[Path, Path]:
    filename_timestamp = render_timestamp_for_filename(payload.ended_at)
    archive_filename = f"{filename_timestamp}_{payload.business}_{payload.assistant_name}.json"
    raw_output_path = archive_root / payload.business / raw_dir_name / archive_filename
    normalized_output_path = archive_root / payload.business / normalized_dir_name / archive_filename
    return raw_output_path, normalized_output_path


def archive_session_payloads(
    archive_root: Path,
    raw_payload: dict,
    normalized_payload: SessionPayload,
    backup_roots: Iterable[Path] | None = None,
    raw_dir_name: str = "_raw",
    normalized_dir_name: str = "_normalized",
) -> tuple[Path, Path]:
    primary_raw_output_path, primary_normalized_output_path = build_archive_paths(
        archive_root,
        normalized_payload,
        raw_dir_name=raw_dir_name,
        normalized_dir_name=normalized_dir_name,
    )

    seen_roots: set[Path] = set()
    for candidate_root in [archive_root, *(backup_roots or [])]:
        resolved_root = candidate_root.resolve()
        if resolved_root in seen_roots:
            continue
        seen_roots.add(resolved_root)

        raw_output_path, normalized_output_path = build_archive_paths(
            candidate_root,
            normalized_payload,
            raw_dir_name=raw_dir_name,
            normalized_dir_name=normalized_dir_name,
        )
        try:
            ensure_directory(raw_output_path.parent)
            ensure_directory(normalized_output_path.parent)
            write_json(raw_output_path, raw_payload)
            write_json(normalized_output_path, payload_as_dict(normalized_payload))
        except OSError as archive_error:
            if resolved_root == archive_root.resolve():
                raise
            print(
                f"warning: archive backup write failed for {candidate_root}: {archive_error}",
                file=sys.stderr,
            )
    return primary_raw_output_path, primary_normalized_output_path
