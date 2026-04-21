# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

from schemas import DeliverableRecord, SessionPayload


def _render_deliverables(deliverables: list[DeliverableRecord]) -> str:
    if not deliverables:
        return "- None"
    rendered_lines = []
    for deliverable in deliverables:
        rendered_lines.append(f"- {deliverable.title} ({deliverable.deliverable_type})")
        if deliverable.local_path:
            rendered_lines.append(f"  - Local path: {deliverable.local_path}")
        if deliverable.google_drive_url:
            rendered_lines.append(f"  - Google Drive: {deliverable.google_drive_url}")
        if deliverable.notion_url:
            rendered_lines.append(f"  - Notion: {deliverable.notion_url}")
        rendered_lines.append(f"  - Status: {deliverable.status}")
    return "\n".join(rendered_lines)


def _render_links(links: list[str]) -> str:
    if not links:
        return "- None"
    return "\n".join(f"- {link}" for link in links)


def _render_routing_metadata(payload: SessionPayload) -> str:
    metadata_lines: list[str] = []
    if payload.delegate_role:
        metadata_lines.append(f"delegate_role: {payload.delegate_role}")
    if payload.origin_assistant_name:
        origin_surface = payload.origin_client_surface or "unknown"
        metadata_lines.append(f"origin: {payload.origin_assistant_name} via {origin_surface}")
    if payload.origin_session_id:
        metadata_lines.append(f"origin_session_id: {payload.origin_session_id}")
    if payload.project_root:
        metadata_lines.append(f"project_root: {payload.project_root}")
    return "\n".join(metadata_lines) if metadata_lines else "None"


def render_google_doc_entry(payload: SessionPayload) -> str:
    return (
        "\n"
        "============================================================\n"
        f"session_id: {payload.session_id}\n"
        f"date_time: {payload.ended_at}\n"
        f"business: {payload.business}\n"
        f"project_name: {payload.project_name}\n"
        f"assistant_name: {payload.assistant_name}\n"
        f"client_surface: {payload.client_surface}\n"
        f"session_type: {payload.session_type}\n"
        f"status: {payload.status}\n"
        "============================================================\n\n"
        "Routing Metadata\n"
        f"{_render_routing_metadata(payload)}\n\n"
        "Session Summary\n"
        f"{payload.session_summary or 'None'}\n\n"
        "Work Completed\n"
        f"{payload.work_completed or 'None'}\n\n"
        "Deliverables\n"
        f"{_render_deliverables(payload.deliverables)}\n\n"
        "Links\n"
        f"{_render_links(payload.links)}\n\n"
        "Next Steps\n"
        f"{payload.next_steps or 'None'}\n\n"
        "Open Questions\n"
        f"{payload.open_questions or 'None'}\n"
    )
