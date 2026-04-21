# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import argparse
import json
import subprocess
import time
import uuid
from pathlib import Path

from cli_broker import (
    BrokerTask,
    broker_task_as_dict,
    get_broker_paths,
    load_broker_settings,
    resolve_route,
    task_file_path,
    worker_heartbeat_path,
    write_broker_task,
)
from common import PYTHON_EXECUTABLE, SCRIPT_DIR, load_runtime_config


WINDOWS_CREATE_NO_WINDOW = 0x08000000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enqueue one brokered CLI task.")
    parser.add_argument("--project-root", default="", help="Project root or current working directory")
    parser.add_argument("--request", default="", help="Task request text")
    parser.add_argument("--request-file", default="", help="Path to a file containing task request text")
    parser.add_argument("--role", default="", help="Named project role, if applicable")
    parser.add_argument("--task-category", default="", help="Explicit task category override")
    parser.add_argument("--context-path", action="append", default=[], help="Extra context file paths")
    parser.add_argument("--origin-assistant-name", default="", help="Origin assistant name override")
    parser.add_argument("--origin-client-surface", default="", help="Origin client surface override")
    parser.add_argument("--origin-session-id", default="", help="Origin session ID for log correlation")
    parser.add_argument("--wait", action="store_true", help="Wait for the broker worker to finish this task")
    parser.add_argument("--timeout-seconds", type=int, default=300, help="Wait timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Print the queued task payload without writing it")
    return parser.parse_args()


def _load_request_text(args: argparse.Namespace) -> str:
    if args.request_file:
        return Path(args.request_file).read_text(encoding="utf-8").strip()
    return args.request.strip()


def _resolve_context_paths(raw_context_paths: list[str]) -> list[str]:
    resolved_paths: list[str] = []
    for raw_context_path in raw_context_paths:
        resolved_path = Path(raw_context_path).resolve()
        if not resolved_path.exists():
            raise RuntimeError(f"Context path does not exist: {resolved_path}")
        resolved_paths.append(str(resolved_path))
    return resolved_paths


def _worker_is_busy(processing_dir: Path) -> bool:
    return any(processing_dir.glob("*.json"))


def _external_worker_is_alive(broker_paths, heartbeat_max_age_seconds: int) -> bool:
    heartbeat_path = worker_heartbeat_path(broker_paths)
    if not heartbeat_path.exists():
        return False
    heartbeat_age_seconds = time.time() - heartbeat_path.stat().st_mtime
    return heartbeat_age_seconds <= heartbeat_max_age_seconds


def _wait_for_result(task_id: str, timeout_seconds: int) -> dict[str, object]:
    runtime_config = load_runtime_config()
    broker_settings = load_broker_settings(runtime_config)
    broker_paths = get_broker_paths(runtime_config)
    deadline = time.time() + timeout_seconds
    done_path = task_file_path(broker_paths.done_dir, task_id)
    failed_path = task_file_path(broker_paths.failed_dir, task_id)
    inbox_path = task_file_path(broker_paths.inbox_dir, task_id)
    processing_path = task_file_path(broker_paths.processing_dir, task_id)
    spawned_rescue_worker = False
    worker_bootstrap_seconds = int(broker_settings.get("wait_worker_bootstrap_seconds", 5))
    heartbeat_max_age_seconds = int(broker_settings.get("wait_worker_heartbeat_max_age_seconds", 15))
    while time.time() < deadline:
        if done_path.exists():
            return json.loads(done_path.read_text(encoding="utf-8"))
        if failed_path.exists():
            failed_payload = json.loads(failed_path.read_text(encoding="utf-8"))
            raise RuntimeError(failed_payload.get("error_text") or f"Broker task failed: {task_id}")
        if (
            not spawned_rescue_worker
            and time.time() + worker_bootstrap_seconds <= deadline
            and inbox_path.exists()
            and not processing_path.exists()
            and not _worker_is_busy(broker_paths.processing_dir)
            and not _external_worker_is_alive(broker_paths, heartbeat_max_age_seconds)
        ):
            subprocess.Popen(
                [PYTHON_EXECUTABLE, str(SCRIPT_DIR / "cli_broker_worker.py"), "--once"],
                cwd=str(SCRIPT_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=WINDOWS_CREATE_NO_WINDOW,
            )
            spawned_rescue_worker = True
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for broker task: {task_id}")


def main() -> None:
    args = parse_args()
    runtime_config = load_runtime_config()
    broker_settings = load_broker_settings(runtime_config)
    broker_paths = get_broker_paths(runtime_config)

    project_root = Path(args.project_root or Path.cwd()).resolve()
    request_text = _load_request_text(args)
    if not request_text:
        raise RuntimeError("Either --request or --request-file is required")

    routing_decision = resolve_route(
        project_root=project_root,
        role=args.role,
        task_category=args.task_category,
        request_text=request_text,
        policy_path=Path(broker_settings["global_policy_path"]).resolve(),
        override_file_name=(broker_settings.get("override_file_name") or "AI_ROUTING.yaml").strip(),
    )

    task = BrokerTask(
        task_id=str(uuid.uuid4()),
        project_root=str(project_root),
        request_text=request_text,
        role=args.role.strip().lower(),
        task_category=routing_decision.task_category,
        context_paths=_resolve_context_paths(args.context_path),
        origin_assistant_name=(args.origin_assistant_name or broker_settings.get("default_origin_assistant_name") or "codex").strip().lower(),
        origin_client_surface=(
            args.origin_client_surface or broker_settings.get("default_origin_client_surface") or "codex-cli"
        ).strip().lower(),
        origin_session_id=args.origin_session_id.strip(),
        provider_hint=routing_decision.provider_id,
        route_reason=routing_decision.reason,
    )

    if args.dry_run:
        print(json.dumps(broker_task_as_dict(task), indent=2))
        return

    task_path = write_broker_task(broker_paths, task)
    if args.wait:
        result_payload = _wait_for_result(task.task_id, args.timeout_seconds)
        print(result_payload.get("output_text") or json.dumps(result_payload, indent=2))
        return

    print(
        json.dumps(
            {
                "task_id": task.task_id,
                "task_file": str(task_path),
                "provider_hint": task.provider_hint,
                "task_category": task.task_category,
                "route_reason": task.route_reason,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
