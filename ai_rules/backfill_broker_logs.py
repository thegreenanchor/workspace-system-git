# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from broker_session_builder import build_broker_payload
from cli_broker import BrokerResult, BrokerTask, ProviderDefinition, get_broker_paths, load_broker_settings, provider_definition
from common import PYTHON_EXECUTABLE, SCRIPT_DIR, load_runtime_config, write_json
from status_store import get_session_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill missing session logs for broker result files.")
    parser.add_argument("--failed-only", action="store_true", help="Only backfill failed broker results.")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be backfilled without submitting.")
    return parser.parse_args()


def _load_result(result_path: Path) -> BrokerResult | None:
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    required_keys = {"task_id", "provider_id", "assistant_name", "client_surface", "status"}
    if not required_keys.issubset(payload.keys()):
        return None
    return BrokerResult(**payload)


def _load_task(task_path: Path) -> BrokerTask:
    payload = json.loads(task_path.read_text(encoding="utf-8"))
    return BrokerTask(**payload)


def _candidate_result_paths(broker_paths, failed_only: bool) -> list[Path]:
    result_paths = [path for path in broker_paths.failed_dir.glob("*.json") if not path.name.endswith("-task.json")]
    if not failed_only:
        result_paths.extend(broker_paths.done_dir.glob("*.json"))
    return sorted(result_paths)


def main() -> None:
    args = parse_args()
    runtime_config = load_runtime_config()
    broker_settings = load_broker_settings(runtime_config)
    broker_paths = get_broker_paths(runtime_config)
    sqlite_path = Path(runtime_config["sqlite"]["path"]).resolve()
    default_business = (runtime_config.get("automation", {}).get("default_business") or "personal").strip().lower()
    policy_path = Path(str(broker_settings["global_policy_path"])).resolve()
    results: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    for result_path in _candidate_result_paths(broker_paths, failed_only=args.failed_only):
        result = _load_result(result_path)
        if result is None:
            continue
        if (result.logging_status or "").strip().lower() == "submitted":
            continue
        if get_session_record(sqlite_path, result.task_id):
            continue

        task_path = broker_paths.failed_dir / f"{result.task_id}-task.json"
        if not task_path.exists():
            continue
        task = _load_task(task_path)
        provider = provider_definition(policy_path, result.provider_id)
        payload = build_broker_payload(task, result, provider, default_business=default_business)
        payload_path = SCRIPT_DIR / "temp_payloads" / f"backfill-broker-{result.task_id}.json"
        write_json(payload_path, payload)
        results.append({"task_id": result.task_id, "payload_file": str(payload_path), "status": result.status})

        if args.dry_run:
            continue

        child_environment = os.environ.copy()
        child_environment["PYTHONIOENCODING"] = "utf-8"
        try:
            subprocess.run(
                [PYTHON_EXECUTABLE, str(SCRIPT_DIR / "submit_session.py"), "--payload-file", str(payload_path)],
                check=True,
                env=child_environment,
            )
        except subprocess.CalledProcessError as exc:
            failures.append(
                {
                    "task_id": result.task_id,
                    "payload_file": str(payload_path),
                    "error": str(exc),
                }
            )
            continue

        result.logging_status = "submitted"
        result.payload_file = str(payload_path)
        write_json(result_path, result)

    print(json.dumps({"count": len(results), "results": results, "failures": failures}, indent=2))


if __name__ == "__main__":
    main()
