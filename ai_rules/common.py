# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = SCRIPT_DIR / "config.yaml"
DEFAULT_ENV_PATH = SCRIPT_DIR.parent / "secrets" / "ai_rules" / ".env"
LEGACY_ENV_PATH = SCRIPT_DIR / ".env"
DEFAULT_PROJECT_ROOTS_PATH = SCRIPT_DIR / "project_roots.yaml"
PYTHON_EXECUTABLE = sys.executable or "python"


def load_runtime_config(config_path: Path = DEFAULT_CONFIG_PATH, env_path: Path = DEFAULT_ENV_PATH) -> dict[str, Any]:
    load_dotenv(env_path if env_path.exists() else LEGACY_ENV_PATH, encoding="utf-8-sig")
    with config_path.open("r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file) or {}


def load_project_roots(project_roots_path: Path = DEFAULT_PROJECT_ROOTS_PATH) -> dict[str, Any]:
    with project_roots_path.open("r", encoding="utf-8") as roots_file:
        return yaml.safe_load(roots_file) or {}


def ensure_directory(directory_path: Path) -> None:
    directory_path.mkdir(parents=True, exist_ok=True)


def require_env_var(env_var_name: str) -> str:
    env_value = os.getenv(env_var_name, "").strip()
    if not env_value:
        raise RuntimeError(f"Missing required environment variable: {env_var_name}")
    return env_value


def write_json(output_path: Path, payload: Any) -> None:
    ensure_directory(output_path.parent)
    with output_path.open("w", encoding="utf-8") as output_file:
        serializable_payload = asdict(payload) if is_dataclass(payload) else payload
        json.dump(serializable_payload, output_file, indent=2, ensure_ascii=True)


def request_json_with_curl_fallback(
    method: str,
    url: str,
    headers: dict[str, str],
    json_body: dict[str, Any] | None = None,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    curl_command = [
        "curl.exe",
        "-4",
        "-sS",
        "-X",
        method.upper(),
        url,
        "--max-time",
        str(timeout_seconds),
        "--write-out",
        "\n__CURL_STATUS__:%{http_code}",
    ]
    for header_name, header_value in headers.items():
        curl_command.extend(["-H", f"{header_name}: {header_value}"])
    curl_input = None
    if json_body is not None:
        curl_command.extend(["--data-binary", "@-"])
        curl_input = json.dumps(json_body, ensure_ascii=True).encode("utf-8")

    completed_process = subprocess.run(
        curl_command,
        input=curl_input,
        capture_output=True,
        text=False,
        timeout=timeout_seconds + 5,
        check=False,
    )
    stdout_text = (completed_process.stdout or b"").decode("utf-8", errors="replace")
    stderr_text = (completed_process.stderr or b"").decode("utf-8", errors="replace")
    if completed_process.returncode != 0:
        failure_text = stderr_text.strip() or stdout_text.strip()
        raise RuntimeError(f"curl transport failure for {method.upper()} {url}: {failure_text}")

    response_text = stdout_text
    status_marker = "\n__CURL_STATUS__:"
    if status_marker not in response_text:
        raise RuntimeError(f"curl response missing status marker for {method.upper()} {url}")

    response_body, status_code_text = response_text.rsplit(status_marker, 1)
    status_code = int(status_code_text.strip() or "0")
    response_body = response_body.strip()

    if status_code >= 400:
        raise RuntimeError(f"Notion API error {status_code} for {method.upper()} {url}: {response_body[:1000]}")
    if not response_body:
        return {}
    return json.loads(response_body)


def _ensure_table_columns(database_connection: sqlite3.Connection, table_name: str, required_columns: dict[str, str]) -> None:
    existing_columns = {
        row[1]
        for row in database_connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    for column_name, column_definition in required_columns.items():
        if column_name not in existing_columns:
            database_connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def init_status_db(sqlite_path: Path) -> sqlite3.Connection:
    ensure_directory(sqlite_path.parent)
    database_connection = sqlite3.connect(sqlite_path)
    database_connection.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            business TEXT NOT NULL,
            project_name TEXT NOT NULL,
            assistant_name TEXT NOT NULL,
            client_surface TEXT NOT NULL,
            session_type TEXT NOT NULL,
            origin_assistant_name TEXT,
            origin_client_surface TEXT,
            origin_session_id TEXT,
            delegate_role TEXT,
            project_root TEXT,
            status TEXT NOT NULL,
            submission_stage TEXT NOT NULL,
            raw_payload_path TEXT NOT NULL,
            normalized_payload_path TEXT NOT NULL,
            notion_page_id TEXT,
            google_doc_id TEXT,
            last_error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    database_connection.execute(
        """
        CREATE TABLE IF NOT EXISTS attempts (
            attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            attempt_number INTEGER NOT NULL,
            status TEXT NOT NULL,
            submission_stage TEXT NOT NULL,
            error_message TEXT,
            attempted_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
        """
    )
    database_connection.execute(
        """
        CREATE TABLE IF NOT EXISTS deliverables (
            deliverable_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            title TEXT NOT NULL,
            deliverable_type TEXT NOT NULL,
            local_path TEXT,
            google_drive_url TEXT,
            notion_url TEXT,
            status TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
        """
    )
    _ensure_table_columns(
        database_connection,
        "sessions",
        {
            "origin_assistant_name": "TEXT",
            "origin_client_surface": "TEXT",
            "origin_session_id": "TEXT",
            "delegate_role": "TEXT",
            "project_root": "TEXT",
        },
    )
    database_connection.commit()
    return database_connection
