# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

from pathlib import Path


BUSINESS_PATH_MARKERS = {
    "mna": ("\\mna\\", "\\brands\\mna\\"),
    "tga": ("\\tga\\", "\\brands\\tga\\"),
    "tgah": ("\\tgah\\", "\\brands\\tgah\\"),
    "shl": ("\\shl\\", "\\brands\\shl\\"),
    "personal": ("\\personal\\", "\\travel\\"),
}
SESSION_TYPE_KEYWORDS = (
    ("review", ("review", "risk", "audit", "regression", "bug", "findings", "refactor")),
    ("planning", ("plan", "roadmap", "strategy", "brainstorm", "outline", "deck", "presentation")),
    ("implementation", ("implement", "build", "create", "wire", "fix", "patch", "migrate", "upgrade", "add", "remove", "convert")),
    ("research", ("research", "investigate", "compare", "look up", "find", "browse", "campaign", "content", "analytics")),
    ("advisory", ("advice", "recommend", "thoughts", "should we", "what should", "opinion")),
)


def infer_business_from_path(current_path: Path) -> str | None:
    normalized_path = str(current_path).replace("/", "\\").lower()
    for business_slug, markers in BUSINESS_PATH_MARKERS.items():
        if any(path_marker in normalized_path for path_marker in markers):
            return business_slug
    return None


def infer_project_name_from_path(current_path: Path) -> str | None:
    project_folder_name = current_path.name.strip().lower()
    return project_folder_name.replace("_", "-") or None


def infer_session_type_from_text(*text_values: str, default: str = "other") -> str:
    combined_text = " ".join((text_value or "").lower() for text_value in text_values)
    for session_type, keywords in SESSION_TYPE_KEYWORDS:
        if any(keyword in combined_text for keyword in keywords):
            return session_type
    return default
