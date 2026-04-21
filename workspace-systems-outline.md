# Workspace Systems Outline

Last updated: 2026-04-08
Root: `<workspace-root>`

This file is a practical map of the workspace and the major systems built inside it. It focuses on projects, automation systems, agent frameworks, skills, and shared infrastructure rather than trying to document every file.

## Top-Level Workspace Layout

- `.claude`
  - Claude-related local config and workspace metadata.
- `ai_rules`
  - Central AI automation, broker, routing, session logging, media-ingest, Notion publishing, and support scripts.
- `archive`
  - Archived workspace material and older project snapshots.
- `businesses`
  - Business-specific workspaces grouped by brand.
- `Demo`
  - Demo or sandbox material.
- `exports`
  - Exported outputs.
- `openclaw`
  - Large agent and skills platform with apps, extensions, packages, UI, server code, and bundled skills.
- `osint-toolkit`
  - OSINT-oriented project with cases, targets, scripts, templates, reports, and tests.
- `powerpoint templates`
  - Presentation templates and related deck assets.
- `projects`
  - General non-business project roots.
- `raw-media-downloads`
  - Downloaded raw media and ingest staging.
- `secrets`
  - Secret-bearing files and protected configuration inputs.
- `shared`
  - Shared standards, templates, and reusable cross-project assets.

## Core Workspace Infrastructure

- Workspace instructions:
  - `AGENTS.md`
- Shared planning/context files:
  - `workspace-game-plan.md`
  - `blog-post-ai-model-routing.md`
  - `codex-prompt-notion-page-ids.md`
  - `sync_context.py`
- Shared standards:
  - `shared/ai-standards/`
  - includes social output rules, naming rules, session closeout rules, Notion formatting rules, and other workspace-wide policies

## `ai_rules` System

Purpose:
- Central orchestration layer for CLI routing, brokered delegation, session submission, Notion publishing, Google Docs logging, and media ingest.

Key components:
- CLI broker and routing:
  - `cli_broker.py`
  - `cli_broker_worker.py`
  - `enqueue_cli_task.py`
  - `global_cli_policy.yaml`
  - `project_roots.yaml`
- Session logging and auto-submit:
  - `submit_session.py`
  - `auto_submit_codex_sessions.py`
  - `codex_session_ingest.py`
  - `status_store.py`
  - `session_log.db`
  - `session_status.db`
- Notion and Google Docs publishing:
  - `notion_writer.py`
  - `media_notion_writer.py`
  - `publish_markdown_to_notion.py`
  - `google_docs_writer.py`
- Media ingest and maintenance:
  - `media_ingest.py`
  - `media_ingest_config.py`
  - `media_ingest_models.py`
  - `media_maintenance.py`
  - `WSL_MEDIA_INGEST_SOP.md`
- Setup and install scripts:
  - `install_ai_broker.ps1`
  - `install_cli_broker_task.ps1`
  - `install_auto_submit_codex_task.ps1`
  - `setup_gemini_broker.ps1`
- Supporting folders:
  - `instruction_templates/`
  - `rule_blocks/`
  - `site/`
  - `samples/`
  - `cli_broker_runtime/`
  - `temp/`
  - `temp_payloads/`
  - `gemini-home/`

Subcomponents with local agent instructions:
- `ai_rules/instruction_templates/AGENTS.md`

## Business Workspaces

### `businesses/mna`

Purpose:
- MNA Healthcare workspace with direct creative production, Instagram recruiting systems, ops, and legacy archives.

Main folders:
- `archive/`
- `assets/`
- `carousel/`
  - MNA job-carousel production lane
  - includes briefs, scratch-pay notes, templates, Photoshop/export helpers, and Notion sync tools
- `MNA_Knowledge_Documents/`
- `ops/`
- `projects/`

Project systems under `businesses/mna/projects`:
- `marketing_team/`
  - marketing-team system with local `AGENTS.md`
- `scoring-models/`
  - scoring-model-related project area
- `travel-mna/`
  - full Instagram recruiting system for `@travelwithmna`
  - includes:
    - `agents/`
    - `assets/`
    - `config/`
    - `docs/`
    - `queue/`
    - `research/`
    - `schedule/`
    - `scripts/`
    - `skills/`
    - `templates/`
  - local orchestrator:
    - `businesses/mna/projects/travel-mna/AGENTS.md`
  - subagents:
    - `agents/analytics/AGENTS.md`
    - `agents/copywriter/AGENTS.md`
    - `agents/designer/AGENTS.md`
    - `agents/researcher/AGENTS.md`
    - `agents/scheduler/AGENTS.md`

Other MNA agent-bearing roots:
- `businesses/mna/archive/marketing-team-drive-legacy-2026-03-14/AGENTS.md`
- `businesses/mna/archive/marketing-team-drive-legacy-2026-03-14/clients/the-green-anchor-marketing-team/AGENTS.md`

### `businesses/tga`

Purpose:
- TGA business workspace with active project, ops, assets, archives, and scoring-models work.

Main folders:
- `archive/`
- `assets/`
- `ops/`
- `projects/`
- `scoring-models/`

Project systems:
- `projects/marketing_team/`
  - local `AGENTS.md`

Other agent-bearing roots:
- `archive/marketing-team-drive-legacy-2026-03-14/AGENTS.md`

### `businesses/tgah`

Purpose:
- TGAH workspace with primary and patch project tracks.

Main folders:
- `archive/`
- `assets/`
- `ops/`
- `projects/`

Project systems:
- `projects/main/`
  - local `AGENTS.md`
- `projects/patch/`
  - local `AGENTS.md`

### `businesses/shl`

Purpose:
- SHL workspace with archive, assets, ops, and main project root.

Main folders:
- `archive/`
- `assets/`
- `ops/`
- `projects/`

Project systems:
- `projects/main/`

## General Project Roots

### `projects/joseinarcadia`

Purpose:
- Large multi-stage content production system with stage-based agent architecture.

Main folders:
- `agents/`
- `catalog/`
- `docs/`
- `scripts/`
- `skills/`
- `workflows/`

Agent system:
- local orchestrator:
  - `projects/joseinarcadia/AGENTS.md`
- stage groups under `agents/`:
  - `discover/`
  - `ingest/`
  - `classify/`
  - `enrich/`
  - `route/`
  - `edit/`
  - `qa/`
  - `export/`
  - `publish/`
  - `measure/`

Notable agent layout:
- discovery:
  - `0-1-trend-scanner`
  - `0-2-competitor-tracker`
  - `0-3-sound-audio-scout`
  - `0-4-inspiration-queue`
- ingest:
  - `1-1-ingest-engine`
  - `1-2-batch-ingest-runner`
  - `1-3-format-negotiator`
  - `1-4-cookie-auth-manager`
  - `1-5-thumbnail-extractor`
- classify:
  - `2-1-auto-classifier`
  - `2-2-content-type-tagger`
  - `2-3-aesthetic-tagger`
  - `2-4-hook-analyzer`
- enrich:
  - `3-1-transcriber`
  - `3-2-creative-summarizer`
  - `3-3-lyric-caption-extractor`
  - `3-4-music-bpm-analyzer`
  - `3-5-scene-detector`
  - `3-6-color-palette-extractor`
  - `3-7-performance-metrics-logger`
- route:
  - `4-1-edit-router`
  - `4-2-project-scaffolder`
  - `4-3-edit-brief-generator`
- edit:
  - `5-1-proxy-generator`
  - `5-2-caption-subtitle-generator`
  - `5-3-music-recommender`
  - `5-4-text-overlay-writer`
  - `5-5-thumbnail-cover-designer`
- qa:
  - `6-1-export-validator`
  - `6-2-dedupe-agent`
  - `6-3-brand-consistency-checker`
- export:
  - `7-1-format-exporter`
  - `7-2-caption-copy-packager`
  - `7-3-notion-project-closer`
- publish:
  - `8-1-publish-scheduler`
  - `8-2-cross-post-adapter`
  - `8-3-publishing-handoff-agent`
- measure:
  - `9-1-post-publish-tracker`
  - `9-2-content-autopsy-agent`
  - `9-3-trend-feedback-loop`

### Other roots under `projects/`

- `cross-country-trip/`
- `edit-projects/`
- `fcb/`
- `message-attachments-backup/`
- `poshmark-to-amazon/`

These are present as project roots but were not identified in this pass as major agent systems with their own `AGENTS.md`.

## `openclaw` System

Purpose:
- Large standalone platform with its own skills ecosystem, extensions, apps, packages, UI, server code, docs, and agent instructions.

Main folders:
- `.agent/`
- `.agents/`
- `apps/`
- `assets/`
- `docs/`
- `extensions/`
- `packages/`
- `scripts/`
- `skills/`
- `src/`
- `test/`
- `ui/`
- `vendor/`

Agent-bearing roots:
- `openclaw/AGENTS.md`
- `openclaw/src/gateway/server-methods/AGENTS.md`
- `openclaw/docs/zh-CN/AGENTS.md`
- `openclaw/docs/reference/templates/AGENTS.md`
- `openclaw/docs/zh-CN/reference/templates/AGENTS.md`

Skills platform:
- primary bundled skills live under `openclaw/skills/`
- extension-provided skills live under:
  - `openclaw/extensions/acpx/skills/`
  - `openclaw/extensions/diffs/skills/`
  - `openclaw/extensions/feishu/skills/`
  - `openclaw/extensions/open-prose/skills/`
  - `openclaw/extensions/tavily/skills/`

Representative built-in skills:
- `1password`
- `apple-notes`
- `apple-reminders`
- `bear-notes`
- `blogwatcher`
- `coding-agent`
- `discord`
- `gemini`
- `github`
- `nano-pdf`
- `notion`
- `obsidian`
- `openai-whisper`
- `session-logs`
- `skill-creator`
- `slack`
- `spotify-player`
- `summarize`
- `tmux`
- `trello`
- `video-frames`
- `voice-call`
- `weather`
- `xurl`

Representative extension skills:
- `acp-router`
- `diffs`
- `feishu-doc`
- `feishu-drive`
- `feishu-perm`
- `feishu-wiki`
- `prose`
- `tavily`

## `osint-toolkit` System

Purpose:
- Investigation and target-analysis toolkit with case structure, reports, scripted workflows, and test coverage.

Main folders:
- `cases/`
- `config/`
- `docs/`
- `notes/`
- `output/`
- `reports/`
- `scripts/`
- `src/`
- `targets/`
- `templates/`
- `tests/`
- `vendor/`
- `.tmp-tests/`
- `venv/`

## Agent Inventory Summary

`AGENTS.md` files discovered in the workspace: `61`

Primary agent-bearing systems:
- workspace root
- `ai_rules/instruction_templates`
- `businesses/mna/projects/travel-mna`
- `businesses/mna/projects/marketing_team`
- `businesses/mna/archive/...`
- `businesses/tga/projects/marketing_team`
- `businesses/tgah/projects/main`
- `businesses/tgah/projects/patch`
- `projects/joseinarcadia`
- `projects/joseinarcadia/agents/*`
- `openclaw`
- `openclaw/src/gateway/server-methods`
- `openclaw/docs/...`

## Skill Inventory Summary

`SKILL.md` files discovered in the workspace: `61`

Primary skill-bearing systems:
- `openclaw/skills/`
- `openclaw/extensions/*/skills/`
- vendor-like bundled skill path under:
  - `ai_rules/gemini-home/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/builtin/`

## Notes

- This outline is intentionally system-focused. It is a map for navigation and maintenance, not a full file manifest.
- The unusual top-level folders `Cï€º` and `Gï€º` appear to be mirrored or imported drive-style directories and should be treated carefully before cleanup or automation work.
- `shared/ai-standards/` and `ai_rules/` are the main policy and automation backbone for the workspace.
- The strongest explicit multi-agent systems in this workspace are:
  - `businesses/mna/projects/travel-mna`
  - `projects/joseinarcadia`
  - `openclaw`
