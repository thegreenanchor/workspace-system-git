# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from broker_session_builder import build_broker_payload
from cli_broker import (
    BrokerResult,
    BrokerTask,
    ProviderDefinition,
    append_worker_log,
    broker_result_as_dict,
    get_broker_paths,
    list_task_files,
    load_broker_settings,
    load_broker_task,
    provider_definition,
    resolve_route,
    task_file_path,
    utc_now_iso,
    worker_heartbeat_path,
    write_broker_result,
)
from common import PYTHON_EXECUTABLE, SCRIPT_DIR, load_runtime_config, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process queued broker tasks.")
    parser.add_argument("--once", action="store_true", help="Process the current queue and exit")
    parser.add_argument("--skip-submit", action="store_true", help="Skip Notion/Google Docs submission for completed tasks")
    parser.add_argument("--mock-output", default="", help="Use a fixed output instead of invoking the target CLI")
    return parser.parse_args()


def _write_worker_heartbeat(broker_paths, status: str, task_id: str = "") -> None:
    write_json(
        worker_heartbeat_path(broker_paths),
        {
            "updated_at": utc_now_iso(),
            "status": status,
            "task_id": task_id,
        },
    )


def _read_text_excerpt(file_path: Path, max_chars: int) -> str:
    if not file_path.exists() or not file_path.is_file():
        return ""
    try:
        return file_path.read_text(encoding="utf-8")[:max_chars].strip()
    except UnicodeDecodeError:
        return ""


PROMPT_PROJECT_MAX_CHARS = 900
PROMPT_ROLE_MAX_CHARS = 1400
PROMPT_CONTEXT_MAX_CHARS = 1200
PROMPT_TOTAL_MAX_CHARS = 6500


def _project_instruction_excerpt(project_root: Path, max_chars: int = PROMPT_PROJECT_MAX_CHARS) -> str:
    for instruction_name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
        instruction_path = project_root / instruction_name
        excerpt_text = _read_text_excerpt(instruction_path, max_chars)
        if excerpt_text:
            return f"{instruction_name}\n{excerpt_text}"
    return ""


def _context_sections(context_paths: list[str], max_chars: int = PROMPT_CONTEXT_MAX_CHARS) -> list[str]:
    context_sections: list[str] = []
    for context_path_text in context_paths:
        context_path = Path(context_path_text)
        excerpt_text = _read_text_excerpt(context_path, max_chars)
        if excerpt_text:
            context_sections.append(f"{context_path}\n{excerpt_text}")
    return context_sections


def build_provider_prompt(task: BrokerTask, provider: ProviderDefinition, role_prompt_path: str) -> str:
    project_root = Path(task.project_root).resolve()
    prompt_sections = [
        "You are being invoked by a local CLI broker.",
        f"Target provider lane: {provider.provider_id}",
        f"Project root: {project_root}",
        f"Role: {task.role or 'none'}",
        f"Task category: {task.task_category or 'implementation'}",
        f"User Request\n{task.request_text.strip()}",
        "Output Contract\n"
        "Return only the requested deliverable.\n"
        "Start immediately with the deliverable content itself.\n"
        "Do not describe your plan, tools, steps, reasoning, or file access.\n"
        "Do not say 'I will', 'first', 'next', or similar meta text.\n"
        "Do not mention the broker, queue, prompt, or task packet.",
    ]

    explicit_context_sections = _context_sections(task.context_paths)
    if explicit_context_sections:
        prompt_sections.append("Context Files\n" + "\n\n".join(explicit_context_sections))

    if role_prompt_path:
        role_prompt_text = _read_text_excerpt(Path(role_prompt_path), PROMPT_ROLE_MAX_CHARS)
        if role_prompt_text:
            prompt_sections.append(f"Role Instructions\n{role_prompt_text}")

    project_instructions = _project_instruction_excerpt(project_root)
    if project_instructions:
        prompt_sections.append(f"Project Instructions\n{project_instructions}")
    prompt_text = "\n\n".join(section for section in prompt_sections if section).strip()
    return prompt_text[:PROMPT_TOTAL_MAX_CHARS]


def invoke_provider(prompt_text: str, provider: ProviderDefinition, timeout_seconds: int, working_directory: Path) -> str:
    executable_path = Path(provider.executable)
    if not executable_path.exists():
        raise RuntimeError(f"Provider executable not found: {provider.executable}")

    command = [provider.executable, *provider.extra_args]
    subprocess_input = None
    if provider.prompt_flag:
        command.append(provider.prompt_flag)
    if provider.prompt_via_stdin:
        # Pass the prompt over stdin to avoid Windows command-length limits.
        command.append("_broker_prompt")
        subprocess_input = prompt_text
    else:
        command.append(prompt_text)

    completed_process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        input=subprocess_input,
        timeout=timeout_seconds,
        check=False,
        cwd=str(working_directory),
    )
    combined_output = "\n".join(
        text_part.strip()
        for text_part in (completed_process.stdout or "", completed_process.stderr or "")
        if text_part and text_part.strip()
    )
    if completed_process.returncode != 0:
        lowered_output = combined_output.lower()
        if (
            "authentication cancelled" in lowered_output
            or "error authenticating" in lowered_output
            or "opening authentication page in your browser" in lowered_output
            or "redirect_uri_mismatch" in lowered_output
        ):
            raise RuntimeError(
                f"{provider.provider_id} is not ready for headless broker use. "
                f"Complete interactive authentication for {provider.client_surface} first."
            )
        raise RuntimeError(
            f"{provider.provider_id} exited with code {completed_process.returncode}: "
            f"{combined_output}"
        )
    output_text = (completed_process.stdout or "").strip()
    if not output_text:
        raise RuntimeError(f"{provider.provider_id} returned no output")
    if "Opening authentication page in your browser." in output_text:
        raise RuntimeError(f"{provider.provider_id} requested interactive browser authentication in headless mode")
    return output_text


def _submit_broker_session(task: BrokerTask, result: BrokerResult, provider: ProviderDefinition, runtime_config: dict) -> tuple[str, str]:
    default_business = (runtime_config.get("automation", {}).get("default_business") or "personal").strip().lower()
    payload = build_broker_payload(task, result, provider, default_business=default_business)
    payload_path = SCRIPT_DIR / "temp_payloads" / f"cli-broker-{task.task_id}.json"
    write_json(payload_path, payload)
    subprocess.run(
        [
            PYTHON_EXECUTABLE,
            str(SCRIPT_DIR / "submit_session.py"),
            "--payload-file",
            str(payload_path),
        ],
        check=True,
    )
    return str(payload_path), "submitted"


def _is_stale_file(file_path: Path, stale_after_minutes: int) -> bool:
    modified_at = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
    stale_cutoff = datetime.now(timezone.utc) - timedelta(minutes=stale_after_minutes)
    return modified_at <= stale_cutoff


def recover_stale_processing_tasks(runtime_config: dict) -> int:
    broker_settings = load_broker_settings(runtime_config)
    stale_after_minutes = int(broker_settings.get("processing_stale_minutes", 20))
    if stale_after_minutes <= 0:
        return 0

    broker_paths = get_broker_paths(runtime_config)
    recovered_count = 0
    for processing_task_path in list_task_files(broker_paths.processing_dir):
        if not _is_stale_file(processing_task_path, stale_after_minutes):
            continue

        inbox_task_path = task_file_path(broker_paths.inbox_dir, processing_task_path.stem)
        stale_task_path = broker_paths.failed_dir / f"{processing_task_path.stem}-task.stale.json"
        shutil.copy2(str(processing_task_path), stale_task_path)
        processing_task_path.replace(inbox_task_path)

        prompt_path = broker_paths.processing_dir / f"{processing_task_path.stem}-prompt.txt"
        if prompt_path.exists():
            stale_prompt_path = broker_paths.failed_dir / f"{processing_task_path.stem}-prompt.stale.txt"
            shutil.move(str(prompt_path), stale_prompt_path)

        append_worker_log(
            broker_paths,
            f"requeued stale task_id={processing_task_path.stem} after {stale_after_minutes}m in processing",
        )
        recovered_count += 1
    return recovered_count


def process_task(
    task_path: Path,
    runtime_config: dict,
    skip_submit: bool,
    mock_output: str,
) -> BrokerResult:
    broker_settings = load_broker_settings(runtime_config)
    broker_paths = get_broker_paths(runtime_config)
    _write_worker_heartbeat(broker_paths, "processing", task_path.stem)
    processing_path = task_file_path(broker_paths.processing_dir, task_path.stem)
    task_path.replace(processing_path)

    task = load_broker_task(processing_path)
    started_at = utc_now_iso()
    routing_decision = resolve_route(
        project_root=Path(task.project_root),
        role=task.role,
        task_category=task.task_category,
        request_text=task.request_text,
        policy_path=Path(broker_settings["global_policy_path"]).resolve(),
        override_file_name=(broker_settings.get("override_file_name") or "AI_ROUTING.yaml").strip(),
    )
    provider = provider_definition(Path(broker_settings["global_policy_path"]).resolve(), routing_decision.provider_id)
    prompt_text = build_provider_prompt(task, provider, routing_decision.role_prompt_path)

    prompt_path = broker_paths.processing_dir / f"{task.task_id}-prompt.txt"
    prompt_path.write_text(prompt_text, encoding="utf-8")

    try:
        output_text = mock_output or invoke_provider(
            prompt_text=prompt_text,
            provider=provider,
            timeout_seconds=int(broker_settings.get("provider_timeout_seconds", 900)),
            working_directory=Path(task.project_root).resolve(),
        )
        completed_at = utc_now_iso()
        output_path = broker_paths.done_dir / f"{task.task_id}.txt"
        output_path.write_text(output_text, encoding="utf-8")
        archived_prompt_path = broker_paths.done_dir / f"{task.task_id}-prompt.txt"
        shutil.move(str(prompt_path), archived_prompt_path)

        result = BrokerResult(
            task_id=task.task_id,
            provider_id=provider.provider_id,
            assistant_name=provider.assistant_name,
            client_surface=provider.client_surface,
            status="completed",
            role=task.role,
            task_category=routing_decision.task_category,
            output_text=output_text,
            artifact_paths=[str(archived_prompt_path), str(output_path)],
            created_at=task.created_at,
            started_at=started_at,
            completed_at=completed_at,
        )

        should_submit = bool(broker_settings.get("submit_sessions", True)) and not skip_submit
        if should_submit:
            try:
                result.payload_file, result.logging_status = _submit_broker_session(task, result, provider, runtime_config)
            except Exception as logging_exception:
                result.status = "completed-with-log-error"
                result.error_text = str(logging_exception)
                result.logging_status = "failed"

        result_path = task_file_path(broker_paths.done_dir, task.task_id)
        write_broker_result(result_path, result)
        append_worker_log(
            broker_paths,
            f"completed task_id={task.task_id} provider={provider.provider_id} status={result.status}",
        )
        _write_worker_heartbeat(broker_paths, "idle")
        processing_path.unlink(missing_ok=True)
        return result
    except Exception as execution_exception:
        completed_at = utc_now_iso()
        failed_prompt_path = broker_paths.failed_dir / f"{task.task_id}-prompt.txt"
        if prompt_path.exists():
            shutil.move(str(prompt_path), failed_prompt_path)

        result = BrokerResult(
            task_id=task.task_id,
            provider_id=provider.provider_id,
            assistant_name=provider.assistant_name,
            client_surface=provider.client_surface,
            status="failed",
            role=task.role,
            task_category=routing_decision.task_category,
            error_text=str(execution_exception),
            artifact_paths=[str(failed_prompt_path)] if failed_prompt_path.exists() else [],
            created_at=task.created_at,
            started_at=started_at,
            completed_at=completed_at,
        )
        failed_result_path = task_file_path(broker_paths.failed_dir, task.task_id)
        should_submit = bool(broker_settings.get("submit_sessions", True)) and not skip_submit
        if should_submit:
            try:
                result.payload_file, result.logging_status = _submit_broker_session(task, result, provider, runtime_config)
            except Exception as logging_exception:
                result.logging_status = "failed"
                if not result.error_text:
                    result.error_text = str(logging_exception)
                else:
                    result.error_text = f"{result.error_text}\n\nLogging failure: {logging_exception}"
        write_broker_result(failed_result_path, result)
        archived_task_path = broker_paths.failed_dir / f"{task.task_id}-task.json"
        shutil.move(str(processing_path), archived_task_path)
        append_worker_log(
            broker_paths,
            f"failed task_id={task.task_id} provider={provider.provider_id} error={result.error_text}",
        )
        _write_worker_heartbeat(broker_paths, "idle")
        return result


def main() -> None:
    args = parse_args()
    runtime_config = load_runtime_config()
    broker_paths = get_broker_paths(runtime_config)
    _write_worker_heartbeat(broker_paths, "polling")
    recovered_count = recover_stale_processing_tasks(runtime_config)
    task_files = list_task_files(broker_paths.inbox_dir)
    results = []
    for task_path in task_files:
        result = process_task(
            task_path=task_path,
            runtime_config=runtime_config,
            skip_submit=args.skip_submit,
            mock_output=args.mock_output.strip(),
        )
        results.append(broker_result_as_dict(result))

    if not task_files:
        _write_worker_heartbeat(broker_paths, "idle")

    print(json.dumps({"recovered": recovered_count, "processed": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    main()
