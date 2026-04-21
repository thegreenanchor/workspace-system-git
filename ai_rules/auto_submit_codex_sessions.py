# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
import os
from pathlib import Path

from codex_session_ingest import build_codex_session_payload, is_timestamp_stale
from common import PYTHON_EXECUTABLE, SCRIPT_DIR, ensure_directory, load_runtime_config, write_json
from status_store import get_session_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-submit closed Codex sessions from local .codex session files.")
    parser.add_argument("--all", action="store_true", help="Process all stale, unsubmitted Codex sessions.")
    parser.add_argument("--latest", action="store_true", help="Process only the most recent stale, unsubmitted Codex session.")
    parser.add_argument("--session-id", default="", help="Process a specific Codex session ID.")
    parser.add_argument("--session-file", default="", help="Process a specific Codex session file path.")
    parser.add_argument("--stale-minutes", type=int, default=0, help="Override the stale threshold in minutes.")
    parser.add_argument("--dry-run", action="store_true", help="Build payloads and print them without submitting.")
    parser.add_argument(
        "--workdir-prefix",
        default="",
        help="Only process sessions whose recorded workdir starts with this path prefix.",
    )
    parser.add_argument(
        "--current-workdir",
        action="store_true",
        help="Shortcut for --workdir-prefix using the current process working directory.",
    )
    return parser.parse_args()


def _iter_session_files(codex_sessions_root: Path) -> list[Path]:
    return sorted(codex_sessions_root.rglob("rollout-*.jsonl"))


def _resolve_target_sessions(
    session_files: list[Path],
    target_session_id: str,
    target_session_file: str,
) -> list[Path]:
    if target_session_file:
        return [Path(target_session_file).resolve()]

    if target_session_id:
        matched_sessions = [session_path for session_path in session_files if target_session_id in session_path.name]
        if not matched_sessions:
            raise RuntimeError(f"Could not find Codex session file for session_id: {target_session_id}")
        return matched_sessions

    return session_files


def _build_payload_file_path(temp_payload_dir: Path, session_id: str) -> Path:
    return temp_payload_dir / f"codex-auto-{session_id}.json"


def _load_state(state_path: Path) -> dict[str, str]:
    if not state_path.exists():
        return {}
    with state_path.open("r", encoding="utf-8") as state_file:
        return json.load(state_file)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_path_prefix(path_text: str) -> str:
    if not path_text.strip():
        return ""
    return str(Path(path_text).resolve()).rstrip("\\/").lower()


def _matches_workdir_prefix(session_workdir: str, workdir_prefix: str) -> bool:
    normalized_prefix = _normalize_path_prefix(workdir_prefix)
    if not normalized_prefix:
        return True
    normalized_workdir = _normalize_path_prefix(session_workdir)
    return normalized_workdir.startswith(normalized_prefix)


def main() -> None:
    args = parse_args()
    runtime_config = load_runtime_config()
    automation_config = runtime_config.get("automation", {})

    codex_sessions_root = Path(automation_config.get("codex_sessions_root", str(Path.home() / ".codex" / "sessions"))).resolve()
    codex_session_index_path = Path(
        automation_config.get("codex_session_index_path", str(Path.home() / ".codex" / "session_index.jsonl"))
    ).resolve()
    state_path = Path(automation_config.get("state_path", str(SCRIPT_DIR / "codex_auto_submit_state.json"))).resolve()
    default_business = (automation_config.get("default_business") or "personal").strip().lower()
    stale_minutes = args.stale_minutes or int(automation_config.get("stale_minutes", 10))
    workdir_prefix = args.workdir_prefix.strip()
    if args.current_workdir:
        workdir_prefix = os.getcwd()

    sqlite_path = Path(runtime_config["sqlite"]["path"]).resolve()
    temp_payload_dir = SCRIPT_DIR / "temp_payloads"
    ensure_directory(temp_payload_dir)

    session_files = _iter_session_files(codex_sessions_root)
    target_sessions = _resolve_target_sessions(
        session_files=session_files,
        target_session_id=args.session_id.strip(),
        target_session_file=args.session_file.strip(),
    )

    direct_target = bool(args.session_id or args.session_file)
    state_payload = _load_state(state_path)
    install_cutoff = (state_payload.get("install_cutoff") or "").strip()
    if not install_cutoff and not direct_target and not args.latest:
        install_cutoff = _utc_now_iso()
        write_json(state_path, {"install_cutoff": install_cutoff})
        print(json.dumps({"bootstrapped": True, "install_cutoff": install_cutoff, "state_path": str(state_path)}, indent=2))
        return

    built_payloads: list[dict[str, str]] = []
    for session_path in target_sessions:
        codex_session = build_codex_session_payload(
            session_path=session_path,
            session_index_path=codex_session_index_path,
            default_business=default_business,
        )

        if not direct_target and not args.latest and install_cutoff and codex_session.latest_event_at < install_cutoff:
            continue

        if not _matches_workdir_prefix(codex_session.workdir, workdir_prefix):
            continue

        if not direct_target and not is_timestamp_stale(
            timestamp_text=codex_session.latest_event_at,
            stale_minutes=stale_minutes,
        ):
            continue

        session_record = get_session_record(sqlite_path, codex_session.raw_payload["session_id"])
        if session_record and session_record["status"] == "submitted":
            continue

        payload_output_path = _build_payload_file_path(temp_payload_dir, codex_session.raw_payload["session_id"])
        write_json(payload_output_path, codex_session.raw_payload)
        built_payloads.append(
            {
                "session_id": codex_session.raw_payload["session_id"],
                "payload_file": str(payload_output_path),
                "thread_name": codex_session.thread_name,
                "updated_at": codex_session.updated_at or codex_session.latest_event_at,
                "workdir": codex_session.workdir,
            }
        )

    built_payloads.sort(key=lambda payload_info: payload_info["updated_at"])
    if args.latest and built_payloads:
        built_payloads = [built_payloads[-1]]

    if args.dry_run:
        print(json.dumps({"count": len(built_payloads), "sessions": built_payloads}, indent=2))
        return

    for payload_info in built_payloads:
        child_environment = os.environ.copy()
        child_environment["PYTHONIOENCODING"] = "utf-8"
        subprocess.run(
            [
                PYTHON_EXECUTABLE,
                str(SCRIPT_DIR / "submit_session.py"),
                "--payload-file",
                payload_info["payload_file"],
            ],
            check=True,
            env=child_environment,
        )
        print(json.dumps(payload_info, indent=2))


if __name__ == "__main__":
    main()
