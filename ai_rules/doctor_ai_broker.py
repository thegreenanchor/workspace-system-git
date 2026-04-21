# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
from pathlib import Path

from cli_broker import get_broker_paths, load_broker_settings, provider_definition
from common import DEFAULT_ENV_PATH, LEGACY_ENV_PATH, load_runtime_config
from session_log_audit import audit_session_logs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check AI broker health and key dependencies.")
    parser.add_argument(
        "--provider-smoke",
        action="append",
        default=[],
        help="Run a live provider smoke test for one or more providers (for example: gemini, claude).",
    )
    parser.add_argument("--audit-logs", action="store_true", help="Audit recent sessions for missing or partial logging.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    return parser.parse_args()


def _ok(name: str, details: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": name, "status": "ok", "details": details}
    payload.update(extra)
    return payload


def _warn(name: str, details: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": name, "status": "warn", "details": details}
    payload.update(extra)
    return payload


def _error(name: str, details: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": name, "status": "error", "details": details}
    payload.update(extra)
    return payload


def _info(name: str, details: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": name, "status": "info", "details": details}
    payload.update(extra)
    return payload


def _schtasks_executable() -> str:
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    return str((system_root / "System32" / "schtasks.exe").resolve())


def _load_install_state(script_dir: Path) -> dict[str, object]:
    state_path = script_dir / "broker_install_state.json"
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _startup_launcher_check(script_dir: Path) -> dict[str, object]:
    startup_dir = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    launcher_path = startup_dir / "AI CLI Broker.vbs"
    expected_worker = str((script_dir / "auto_cli_broker_worker.cmd").resolve())
    if not launcher_path.exists():
        return _warn("startup_launcher", "Startup launcher is missing.", path=str(launcher_path))
    launcher_text = launcher_path.read_text(encoding="ascii", errors="replace")
    if expected_worker not in launcher_text:
        return _warn(
            "startup_launcher",
            "Startup launcher exists but does not point at the expected broker worker.",
            path=str(launcher_path),
            expected_worker=expected_worker,
        )
    return _ok("startup_launcher", "Startup launcher points at the broker worker.", path=str(launcher_path))


def _scheduled_task_check(task_name: str, startup_ok: bool, install_state: dict[str, object]) -> dict[str, object]:
    completed_process = subprocess.run(
        [_schtasks_executable(), "/Query", "/TN", task_name, "/V", "/FO", "LIST"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    combined_output = "\n".join(
        text_part.strip()
        for text_part in (completed_process.stdout or "", completed_process.stderr or "")
        if text_part and text_part.strip()
    )
    if completed_process.returncode == 0:
        task_state = ""
        last_result = ""
        for line in (completed_process.stdout or "").splitlines():
            if ":" not in line:
                continue
            label, value = line.split(":", 1)
            normalized_label = label.strip().lower()
            normalized_value = value.strip()
            if normalized_label == "scheduled task state":
                task_state = normalized_value
            elif normalized_label == "last result":
                last_result = normalized_value
        details = "Scheduled task is registered."
        if task_state:
            details = f"Scheduled task is registered and {task_state.lower()}."
        return _ok(
            "scheduled_task",
            details,
            task_name=task_name,
            task_state=task_state or None,
            last_result=last_result or None,
        )
    installed_task_name = str(install_state.get("scheduled_task_name") or "").strip()
    installed_at = str(install_state.get("scheduled_task_installed_at") or "").strip()
    if installed_task_name == task_name and installed_at:
        return _ok(
            "scheduled_task",
            "Scheduled task install is recorded in local broker state, but this shell cannot query it directly.",
            task_name=task_name,
            installed_at=installed_at,
            query_error=combined_output or None,
        )
    if "access is denied" in combined_output.lower():
        return _info(
            "scheduled_task",
            "Scheduled task could not be created or queried from this shell. Startup autostart is the supported path on this machine.",
            task_name=task_name,
        )
    if startup_ok:
        return _info(
            "scheduled_task",
            "Scheduled task is not registered. Startup autostart is already covering the broker launch path.",
            task_name=task_name,
        )
    return _warn("scheduled_task", "Scheduled task is not registered.", task_name=task_name)


def _queue_dirs_check(runtime_config: dict[str, object]) -> dict[str, object]:
    broker_paths = get_broker_paths(runtime_config)
    missing_paths = [
        str(path)
        for path in (
            broker_paths.root_dir,
            broker_paths.inbox_dir,
            broker_paths.processing_dir,
            broker_paths.done_dir,
            broker_paths.failed_dir,
            broker_paths.logs_dir,
        )
        if not path.exists()
    ]
    if missing_paths:
        return _error("queue_dirs", "One or more broker runtime directories are missing.", missing_paths=missing_paths)
    return _ok("queue_dirs", "Broker runtime directories are present.", root_dir=str(broker_paths.root_dir))


def _sqlite_check(sqlite_path: Path) -> dict[str, object]:
    try:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        database_connection = sqlite3.connect(sqlite_path)
        database_connection.execute("SELECT 1")
        database_connection.close()
    except Exception as exc:
        return _error("sqlite", f"SQLite check failed: {exc}", path=str(sqlite_path))
    return _ok("sqlite", "SQLite file is reachable.", path=str(sqlite_path))


def _archive_root_check(archive_root: Path) -> dict[str, object]:
    try:
        archive_root.mkdir(parents=True, exist_ok=True)
        probe_path = archive_root / ".doctor-write-test"
        probe_path.write_text("ok", encoding="utf-8")
        probe_path.unlink(missing_ok=True)
    except Exception as exc:
        return _error("archive_root", f"Archive root is not writable: {exc}", path=str(archive_root))
    return _ok("archive_root", "Archive root is writable.", path=str(archive_root))


def _env_check() -> dict[str, object]:
    env_path = DEFAULT_ENV_PATH if DEFAULT_ENV_PATH.exists() else LEGACY_ENV_PATH
    required_vars = [
        "NOTION_TOKEN",
        "NOTION_VERSION",
        "GOOGLE_OAUTH_CLIENT_FILE",
        "GOOGLE_OAUTH_TOKEN_FILE",
    ]
    missing_vars = [env_var for env_var in required_vars if not os.environ.get(env_var, "").strip()]
    if missing_vars:
        return _error("env", "Required environment variables are missing.", env_path=str(env_path), missing=missing_vars)
    return _ok("env", "Required environment variables are loaded.", env_path=str(env_path))


def _provider_executable_check(policy_path: Path, provider_id: str) -> dict[str, object]:
    try:
        provider = provider_definition(policy_path, provider_id)
    except Exception as exc:
        return _error(f"provider:{provider_id}", f"Provider definition failed: {exc}")
    executable_path = Path(provider.executable)
    if not executable_path.exists():
        return _error(
            f"provider:{provider_id}",
            "Provider executable is missing.",
            executable=str(executable_path),
        )
    return _ok(
        f"provider:{provider_id}",
        "Provider executable exists.",
        executable=str(executable_path),
        client_surface=provider.client_surface,
    )


def _provider_smoke_check(policy_path: Path, provider_id: str) -> dict[str, object]:
    try:
        provider = provider_definition(policy_path, provider_id)
    except Exception as exc:
        return _error(f"provider_smoke:{provider_id}", f"Provider definition failed: {exc}")

    smoke_prompt = "Reply with exactly BROKER_DOCTOR_OK"
    command = [provider.executable, *provider.extra_args]
    if provider.prompt_flag:
        command.append(provider.prompt_flag)
    subprocess_input = None
    if provider.prompt_via_stdin:
        command.append("_broker_prompt")
        subprocess_input = smoke_prompt
    else:
        command.append(smoke_prompt)

    completed_process = subprocess.run(
        command,
        input=subprocess_input,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    combined_output = "\n".join(
        text_part.strip()
        for text_part in (completed_process.stdout or "", completed_process.stderr or "")
        if text_part and text_part.strip()
    )
    if completed_process.returncode != 0:
        return _error(
            f"provider_smoke:{provider_id}",
            f"Provider smoke test failed: {combined_output}",
        )
    if "BROKER_DOCTOR_OK" not in (completed_process.stdout or ""):
        return _warn(
            f"provider_smoke:{provider_id}",
            "Provider responded, but the smoke-test output did not match exactly.",
            output=(completed_process.stdout or "").strip(),
        )
    return _ok(f"provider_smoke:{provider_id}", "Provider smoke test passed.")


def _session_log_audit_check(runtime_config: dict[str, object]) -> dict[str, object]:
    audit_payload = audit_session_logs(runtime_config)
    if (
        not audit_payload["missing_codex_sessions"]
        and not audit_payload["retry_candidates"]
        and not audit_payload["broker_logging_gaps"]
        and not audit_payload["broker_failed_logs"]
    ):
        return _ok("session_log_audit", "No recent session logging gaps detected.", recent_hours=audit_payload["recent_hours"])

    return _warn(
        "session_log_audit",
        "Recent session logging gaps detected.",
        recent_hours=audit_payload["recent_hours"],
        missing_codex_sessions=audit_payload["missing_codex_sessions"][:10],
        retry_candidates=audit_payload["retry_candidates"][:10],
        broker_logging_gaps=audit_payload["broker_logging_gaps"][:10],
        broker_failed_logs=audit_payload["broker_failed_logs"][:10],
    )


def _summarize_status(checks: list[dict[str, object]]) -> str:
    statuses = {str(check["status"]) for check in checks}
    if "error" in statuses:
        return "broken"
    if "warn" in statuses:
        return "degraded"
    return "healthy"


def main() -> None:
    args = parse_args()
    runtime_config = load_runtime_config()
    broker_settings = load_broker_settings(runtime_config)
    policy_path = Path(str(broker_settings["global_policy_path"])).resolve()
    script_dir = Path(__file__).resolve().parent
    install_state = _load_install_state(script_dir)
    startup_check = _startup_launcher_check(script_dir)
    startup_ok = str(startup_check["status"]) == "ok"
    checks = [
        startup_check,
        _scheduled_task_check(
            str(broker_settings.get("schedule_task_name") or "AI CLI Broker"),
            startup_ok=startup_ok,
            install_state=install_state,
        ),
        _queue_dirs_check(runtime_config),
        _sqlite_check(Path(str(runtime_config["sqlite"]["path"])).resolve()),
        _archive_root_check(Path(str(runtime_config["archive"]["root_dir"])).resolve()),
        _env_check(),
        _provider_executable_check(policy_path, "gemini"),
        _provider_executable_check(policy_path, "claude"),
        _provider_executable_check(policy_path, "codex"),
    ]

    for provider_id in args.provider_smoke:
        checks.append(_provider_smoke_check(policy_path, provider_id.strip().lower()))
    if args.audit_logs:
        checks.append(_session_log_audit_check(runtime_config))

    summary = {"status": _summarize_status(checks), "checks": checks}
    if args.json:
        print(json.dumps(summary, indent=2))
        return

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
