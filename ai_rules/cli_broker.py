# Purpose:
# Inputs:
# Outputs:
# Dependencies:
# Notes:

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from common import ensure_directory, load_runtime_config, write_json


TASK_CATEGORY_KEYWORDS = {
    "research": ("research", "investigate", "compare", "brief", "trend", "market", "audience"),
    "google-stack": ("google", "ga4", "analytics", "search console", "workspace", "drive", "docs"),
    "content": ("content", "campaign", "social", "caption", "seo", "topic cluster", "calendar"),
    "analytics": ("metric", "dashboard", "conversion", "traffic", "engagement", "report"),
    "review": ("review", "audit", "risk", "regression", "findings", "qa"),
    "refactor": ("refactor", "cleanup", "harden", "simplify", "rewrite"),
    "presentation": ("presentation", "deck", "slides", "slide", "leadership update"),
    "implementation": ("implement", "build", "wire", "fix", "patch", "script", "automation"),
}
TASK_CATEGORY_PRIORITY = {
    "review": 80,
    "refactor": 70,
    "presentation": 60,
    "analytics": 50,
    "google-stack": 40,
    "research": 30,
    "content": 20,
    "implementation": 10,
}
ROLE_CATEGORY_HINTS = {
    "content-strategist": "content",
    "social-media-specialist": "content",
    "data-analyst": "analytics",
    "presentation-specialist": "presentation",
}


@dataclass
class BrokerPaths:
    root_dir: Path
    inbox_dir: Path
    processing_dir: Path
    done_dir: Path
    failed_dir: Path
    logs_dir: Path


def worker_heartbeat_path(paths: BrokerPaths) -> Path:
    return paths.logs_dir / "worker-heartbeat.json"


@dataclass
class ProviderDefinition:
    provider_id: str
    executable: str
    assistant_name: str
    client_surface: str
    prompt_flag: str = "-p"
    extra_args: list[str] = field(default_factory=list)
    prompt_via_stdin: bool = False


@dataclass
class RoutingDecision:
    provider_id: str
    task_category: str
    reason: str
    project_override_path: str = ""
    role_prompt_path: str = ""


@dataclass
class BrokerTask:
    task_id: str
    project_root: str
    request_text: str
    role: str = ""
    task_category: str = ""
    context_paths: list[str] = field(default_factory=list)
    origin_assistant_name: str = "codex"
    origin_client_surface: str = "codex-cli"
    origin_session_id: str = ""
    created_at: str = ""
    provider_hint: str = ""
    route_reason: str = ""


@dataclass
class BrokerResult:
    task_id: str
    provider_id: str
    assistant_name: str
    client_surface: str
    status: str
    role: str = ""
    task_category: str = ""
    output_text: str = ""
    error_text: str = ""
    artifact_paths: list[str] = field(default_factory=list)
    payload_file: str = ""
    logging_status: str = ""
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_broker_settings(runtime_config: dict[str, Any] | None = None) -> dict[str, Any]:
    runtime_config = runtime_config or load_runtime_config()
    return runtime_config.get("broker", {})


def get_broker_paths(runtime_config: dict[str, Any] | None = None) -> BrokerPaths:
    broker_settings = load_broker_settings(runtime_config)
    root_dir = Path(broker_settings["root_dir"]).resolve()
    paths = BrokerPaths(
        root_dir=root_dir,
        inbox_dir=root_dir / "inbox",
        processing_dir=root_dir / "processing",
        done_dir=root_dir / "done",
        failed_dir=root_dir / "failed",
        logs_dir=root_dir / "logs",
    )
    ensure_broker_dirs(paths)
    return paths


def ensure_broker_dirs(paths: BrokerPaths) -> None:
    for directory_path in (
        paths.root_dir,
        paths.inbox_dir,
        paths.processing_dir,
        paths.done_dir,
        paths.failed_dir,
        paths.logs_dir,
    ):
        ensure_directory(directory_path)


def append_worker_log(paths: BrokerPaths, message_text: str) -> None:
    log_path = paths.logs_dir / "worker.log"
    existing_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    log_path.write_text(f"{existing_text}[{utc_now_iso()}] {message_text}\n", encoding="utf-8")


def load_global_policy(policy_path: Path) -> dict[str, Any]:
    with policy_path.open("r", encoding="utf-8") as policy_file:
        return yaml.safe_load(policy_file) or {}


def find_project_override(start_path: Path, override_file_name: str) -> Path | None:
    resolved_path = start_path.resolve()
    for candidate_root in (resolved_path, *resolved_path.parents):
        override_path = candidate_root / override_file_name
        if override_path.exists():
            return override_path
    return None


def load_project_override(start_path: Path, override_file_name: str) -> tuple[dict[str, Any], Path | None]:
    override_path = find_project_override(start_path, override_file_name)
    if not override_path:
        return {}, None
    with override_path.open("r", encoding="utf-8") as override_file:
        return yaml.safe_load(override_file) or {}, override_path


def classify_task_category(role: str, task_category: str, request_text: str) -> str:
    explicit_category = (task_category or "").strip().lower()
    if explicit_category:
        return explicit_category

    role_name = (role or "").strip().lower()
    if role_name in ROLE_CATEGORY_HINTS:
        return ROLE_CATEGORY_HINTS[role_name]

    combined_text = f"{role_name} {request_text or ''}".lower()
    category_scores: list[tuple[int, int, str]] = []

    for category_name, keywords in TASK_CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in combined_text)
        if score > 0:
            category_scores.append((score, TASK_CATEGORY_PRIORITY.get(category_name, 0), category_name))

    if category_scores:
        category_scores.sort(reverse=True)
        return category_scores[0][2]

    return "implementation"


def resolve_route(
    project_root: Path,
    role: str,
    task_category: str,
    request_text: str,
    policy_path: Path,
    override_file_name: str,
) -> RoutingDecision:
    global_policy = load_global_policy(policy_path)
    project_override, override_path = load_project_override(project_root, override_file_name)
    resolved_role = (role or "").strip().lower()
    resolved_category = classify_task_category(resolved_role, task_category, request_text)

    if resolved_role:
        role_config = (project_override.get("roles") or {}).get(resolved_role)
        if role_config:
            if isinstance(role_config, str):
                provider_id = role_config.strip().lower()
                prompt_file = ""
            else:
                provider_id = (role_config.get("provider") or "").strip().lower()
                prompt_file = (role_config.get("prompt_file") or "").strip()

            role_prompt_path = ""
            if prompt_file and override_path:
                role_prompt_path = str((override_path.parent / prompt_file).resolve())
            return RoutingDecision(
                provider_id=provider_id,
                task_category=resolved_category,
                reason=f"project override for role {resolved_role}",
                project_override_path=str(override_path) if override_path else "",
                role_prompt_path=role_prompt_path,
            )

    override_defaults = project_override.get("defaults") or {}
    override_task_category_map = override_defaults.get("task_categories") or {}
    override_provider_id = (
        override_task_category_map.get(resolved_category)
        or override_defaults.get("provider")
        or ""
    ).strip().lower()

    if override_provider_id:
        override_reason = (
            f"project override for task-category {resolved_category}"
            if resolved_category in override_task_category_map
            else "project override default"
        )
        return RoutingDecision(
            provider_id=override_provider_id,
            task_category=resolved_category,
            reason=override_reason,
            project_override_path=str(override_path) if override_path else "",
        )

    defaults = global_policy.get("defaults") or {}
    task_category_map = defaults.get("task_categories") or {}
    provider_id = (task_category_map.get(resolved_category) or defaults.get("provider") or "codex").strip().lower()
    return RoutingDecision(
        provider_id=provider_id,
        task_category=resolved_category,
        reason=f"global task-category default for {resolved_category}",
        project_override_path=str(override_path) if override_path else "",
    )


def provider_definition(policy_path: Path, provider_id: str) -> ProviderDefinition:
    global_policy = load_global_policy(policy_path)
    provider_config = (global_policy.get("providers") or {}).get(provider_id)
    if not provider_config:
        raise RuntimeError(f"Unknown provider_id in global policy: {provider_id}")
    return ProviderDefinition(
        provider_id=provider_id,
        executable=(provider_config.get("executable") or "").strip(),
        assistant_name=(provider_config.get("assistant_name") or provider_id).strip().lower(),
        client_surface=(provider_config.get("client_surface") or provider_id).strip().lower(),
        prompt_flag=(provider_config.get("prompt_flag") or "-p").strip(),
        extra_args=[str(arg) for arg in (provider_config.get("extra_args") or [])],
        prompt_via_stdin=bool(provider_config.get("prompt_via_stdin", False)),
    )


def task_file_path(queue_dir: Path, task_id: str) -> Path:
    return queue_dir / f"{task_id}.json"


def list_task_files(queue_dir: Path) -> list[Path]:
    return sorted(queue_dir.glob("*.json"))


def write_broker_task(paths: BrokerPaths, task: BrokerTask) -> Path:
    if not task.created_at:
        task.created_at = utc_now_iso()
    task_path = task_file_path(paths.inbox_dir, task.task_id)
    write_json(task_path, task)
    return task_path


def load_broker_task(task_path: Path) -> BrokerTask:
    with task_path.open("r", encoding="utf-8") as task_file:
        task_payload = yaml.safe_load(task_file) or {}
    return BrokerTask(**task_payload)


def write_broker_result(result_path: Path, result: BrokerResult) -> None:
    write_json(result_path, result)


def broker_task_as_dict(task: BrokerTask) -> dict[str, Any]:
    return asdict(task)


def broker_result_as_dict(result: BrokerResult) -> dict[str, Any]:
    return asdict(result)
