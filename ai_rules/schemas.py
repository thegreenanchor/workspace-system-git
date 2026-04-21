# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

from dataclasses import dataclass, field


BUSINESS_VALUES = {"mna", "tga", "tgah", "shl", "personal"}
SESSION_TYPE_VALUES = {"advisory", "planning", "implementation", "review", "research", "other"}
STATUS_VALUES = {"submitted", "partial", "failed", "retry-needed"}
SUBMISSION_STAGE_VALUES = {"notion", "google-doc", "archive", "complete"}


@dataclass
class DeliverableRecord:
    title: str
    deliverable_type: str
    local_path: str = ""
    google_drive_url: str = ""
    notion_url: str = ""
    status: str = "submitted"


@dataclass
class SessionPayload:
    session_id: str
    business: str
    project_name: str
    assistant_name: str
    client_surface: str
    session_type: str
    started_at: str
    ended_at: str
    status: str
    submission_stage: str
    session_summary: str
    work_completed: str
    deliverables: list[DeliverableRecord] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    next_steps: str = ""
    open_questions: str = ""
    full_transcript: str = ""
    origin_assistant_name: str = ""
    origin_client_surface: str = ""
    origin_session_id: str = ""
    delegate_role: str = ""
    project_root: str = ""
