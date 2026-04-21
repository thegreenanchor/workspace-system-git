# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

import re
from pathlib import Path

from cli_broker import BrokerResult, BrokerTask, ProviderDefinition
from inference import infer_business_from_path, infer_project_name_from_path, infer_session_type_from_text


URL_PATTERN = re.compile(r"https?://[^\s)>\]]+")


def _first_paragraph(text_value: str, fallback_text: str) -> str:
    normalized_text = (text_value or "").strip()
    if not normalized_text:
        return fallback_text
    return normalized_text.split("\n\n", 1)[0].strip() or fallback_text


def _extract_links(*text_values: str) -> list[str]:
    seen_links: set[str] = set()
    ordered_links: list[str] = []
    for text_value in text_values:
        for link_url in URL_PATTERN.findall(text_value or ""):
            if link_url not in seen_links:
                seen_links.add(link_url)
                ordered_links.append(link_url)
    return ordered_links


def _extract_next_steps(output_text: str) -> str:
    for paragraph_text in (output_text or "").split("\n\n"):
        cleaned_paragraph = paragraph_text.strip()
        lowered_paragraph = cleaned_paragraph.lower()
        if lowered_paragraph.startswith("next steps") or lowered_paragraph.startswith("if you want"):
            return cleaned_paragraph
    return ""


def _render_transcript(task: BrokerTask, result: BrokerResult) -> str:
    user_header = f"[{task.created_at}] USER via {task.origin_client_surface or 'unknown'}"
    assistant_header = f"[{result.completed_at}] ASSISTANT via {result.client_surface or 'unknown'}"
    metadata_lines = []
    if task.role:
        metadata_lines.append(f"role: {task.role}")
    if result.task_category:
        metadata_lines.append(f"task_category: {result.task_category}")
    if task.project_root:
        metadata_lines.append(f"project_root: {task.project_root}")
    metadata_block = "\n".join(metadata_lines).strip()
    request_block = task.request_text.strip()
    if metadata_block:
        request_block = f"{metadata_block}\n\n{request_block}"
    assistant_body = (result.output_text or "").strip()
    if not assistant_body and result.error_text.strip():
        assistant_body = f"BROKER TASK FAILED\n\n{result.error_text.strip()}"
    return f"{user_header}\n{request_block}\n\n{assistant_header}\n{assistant_body}"


def build_broker_payload(
    task: BrokerTask,
    result: BrokerResult,
    provider: ProviderDefinition,
    default_business: str = "personal",
) -> dict[str, object]:
    project_root = Path(task.project_root).resolve()
    business = infer_business_from_path(project_root) or default_business
    project_name = infer_project_name_from_path(project_root) or "broker-task"

    deliverables = []
    for artifact_path in result.artifact_paths:
        artifact = Path(artifact_path)
        if artifact.suffix.lower() in {".txt", ".md"} and artifact.name == f"{task.task_id}.txt":
            deliverables.append(
                {
                    "title": f"{task.role or result.task_category or provider.provider_id} broker output",
                    "deliverable_type": "broker-output",
                    "local_path": str(artifact),
                    "status": "submitted",
                }
            )

    session_summary = _first_paragraph(
        task.request_text,
        fallback_text=f"Brokered {result.task_category or 'general'} task for {project_name}.",
    )
    work_completed = _first_paragraph(
        result.output_text or result.error_text,
        fallback_text=f"Completed brokered {result.task_category or 'general'} task for {project_name}.",
    )
    if result.error_text.strip():
        work_completed = _first_paragraph(
            f"Broker task failed: {result.error_text.strip()}",
            fallback_text=f"Broker task failed for {project_name}.",
        )
    return {
        "session_id": task.task_id,
        "business": business,
        "project_name": project_name,
        "assistant_name": provider.assistant_name,
        "client_surface": provider.client_surface,
        "session_type": infer_session_type_from_text(task.role, result.task_category, task.request_text, result.output_text),
        "started_at": task.created_at,
        "ended_at": result.completed_at,
        "status": "submitted",
        "submission_stage": "archive",
        "session_summary": session_summary,
        "work_completed": work_completed,
        "deliverables": deliverables,
        "links": _extract_links(task.request_text, result.output_text),
        "next_steps": _extract_next_steps(result.output_text),
        "open_questions": "",
        "full_transcript": _render_transcript(task, result),
        "origin_assistant_name": task.origin_assistant_name,
        "origin_client_surface": task.origin_client_surface,
        "origin_session_id": task.origin_session_id,
        "delegate_role": task.role,
        "project_root": str(project_root),
    }
