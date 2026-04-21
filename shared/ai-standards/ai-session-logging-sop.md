# AI Broker and Session Logging SOP

## Purpose
Define the production operating procedure for the local AI broker, routed provider execution, and session logging pipeline so the system runs predictably and every meaningful session is captured, auditable, and recoverable.

## Scope
This SOP applies to:
- brokered Gemini, Claude, and Codex tasks launched through `ai_rules`
- Codex session auto-submit flows
- manual fallback submission for weaker AI clients
- Notion, Google Docs, local archive, and SQLite session logging
- Windows autostart and health verification for the broker

This SOP does not replace tool-specific operating guides such as `WSL_MEDIA_INGEST_SOP.md`.

## System definition
The system is a local-first routed AI execution and logging stack with these layers:
- routing policy via `global_cli_policy.yaml` and optional project `AI_ROUTING.yaml`
- provider execution via the broker queue in `cli_broker_runtime`
- session normalization and submission via `submit_session.py`
- system-of-record logging to Notion, Google Docs, local JSON archive, and SQLite
- recovery and audit via retry, backfill, and doctor commands

## Canonical paths
- Tooling root: `<workspace-root>\ai_rules`
- Standards root: `<workspace-root>\shared\ai-standards`
- Config: `<workspace-root>\ai_rules\config.yaml`
- Secrets env file: `<workspace-root>\secrets\ai_rules\.env`
- Broker runtime root: `<workspace-root>\ai_rules\cli_broker_runtime`
- Status database: `<workspace-root>\ai_rules\session_log.db`
- Local archive root: `<workspace-root>\archive\session-logs`
- Drive backup archive root: `<drive-backup-root>\Archive\shared\session-logs`
- Codex session root: `<codex-session-root>`
- Codex auto-submit state: `<workspace-root>\ai_rules\codex_auto_submit_state.json`
- Broker install state: `<workspace-root>\ai_rules\broker_install_state.json`

## Meaningful session policy
Log every meaningful AI session.

A meaningful session is any interaction that produces one or more of the following:
- a file change
- a deliverable
- a decision
- a troubleshooting result
- a brokered handoff
- a reusable answer or documented outcome

Do not rely on memory or habit for logging. Logging is part of the execution path.

## System of record
The logging system writes one normalized session payload through four storage targets:
- Notion page in the AI Session Log database
- Google Doc append to the business-specific running log
- local archive copy in raw and normalized JSON
- SQLite status and attempt history in `session_log.db`

The target state for a successful session is:
- `status = submitted`
- `submission_stage = complete`
- `notion_page_id` populated
- `google_doc_id` populated when the business has a configured doc
- raw and normalized archive files present

## Logging policy by client type
### Tool-capable clients
Tool-capable clients must log automatically through the pipeline.

This includes:
- brokered provider runs
- Codex sessions eligible for auto-submit
- local scripts or agents that can call `submit_session.py`

### Weaker clients
Clients without direct local tool access must end with a structured closeout and use manual submission.

The fallback path is:
1. produce the human-readable closeout
2. capture the structured payload
3. submit via `manual_submit.py`
4. confirm the record reaches `submitted` and `complete`

## Broker architecture
The broker uses a filesystem queue under `cli_broker_runtime` with these directories:
- `inbox`
- `processing`
- `done`
- `failed`
- `logs`

Normal flow:
1. `enqueue_cli_task.py` writes a task payload into `inbox`
2. `cli_broker_worker.py` pulls the task into `processing`
3. the worker resolves routing and launches the target provider
4. the result is written to `done` or `failed`
5. if broker submission is enabled, the worker builds a session payload and submits it through the logging pipeline

Recovery behavior:
- stale `processing` tasks are re-queued automatically after the configured timeout
- `--wait` can bootstrap a one-off worker when no background worker is active
- failed broker results can be backfilled later through the session logging pipeline

## Routing policy
Provider routing is controlled by:
- `global_cli_policy.yaml` for defaults
- `AI_ROUTING.yaml` for project-level overrides

Routing decisions must remain explicit and reproducible. Do not hardcode project-specific behavior into broker scripts when it belongs in routing policy.

## Notion design
The Notion AI Session Log database is the primary human-readable system of record.

Each session creates one database page with:
- structured properties for metadata and status
- a page body with the normalized narrative

Page body order:
1. Session Summary
2. Work Completed
3. Routing Metadata when present
4. Deliverables
5. Links
6. Next Steps
7. Open Questions
8. Full Transcript

## Google Docs design
Google Docs provides an append-only readable business log.

Rules:
- one Google Doc per business
- append summary-oriented content, not the full raw transcript
- keep this output readable for review and historical scanning

Google Docs is not the source of truth for retry state. SQLite is.

## Archive design
The archive stores:
- raw payload JSON
- normalized payload JSON

Archive requirements:
- archive locally first
- mirror to configured Drive backup roots on a best-effort basis
- never treat Drive mirror failure as equivalent to total logging failure if local archive succeeded

## SQLite design
SQLite tracks:
- session rows
- attempt history
- deliverable metadata

SQLite is the operational truth for:
- current submission status
- retry-needed sessions
- partial sessions
- failed sessions
- normalized payload paths used for retry

## Authentication requirements
### Notion
- `NOTION_TOKEN` must be present in the secrets env file
- `NOTION_VERSION` must be present in the secrets env file

### Google Docs
- use desktop OAuth credentials, not service-account key JSON
- `GOOGLE_OAUTH_CLIENT_FILE` must point at the desktop OAuth client JSON
- `GOOGLE_OAUTH_TOKEN_FILE` must point at the reusable local token cache
- the first live Google Docs write must complete the browser consent flow

### Providers
Each routed provider must have a verified executable and a usable auth state.

Current expected providers:
- Gemini
- Claude
- Codex

## Install and bootstrap
Use the one-command installer for standard setup.

```powershell
powershell -ExecutionPolicy Bypass -File <workspace-root>\ai_rules\install_ai_broker.ps1
```

Expected install responsibilities:
- create runtime directories
- install Startup autostart
- optionally attempt scheduled task registration
- optionally run Gemini setup
- optionally run the doctor

## Gemini setup
Use the Gemini setup script to verify executable, broker home, and cached auth.

```powershell
powershell -ExecutionPolicy Bypass -File <workspace-root>\ai_rules\setup_gemini_broker.ps1
```

If a non-interactive shell cannot validate Gemini auth cleanly, run the setup from a normal desktop shell and complete the interactive flow once.

## Autostart policy
The broker should start automatically at login.

Supported autostart paths:
- current-user Startup launcher via `install_startup_broker.ps1`
- Windows Scheduled Task via `install_cli_broker_task.ps1`

Operational rules:
- Startup is a supported fallback and remains valid even if Task Scheduler is unavailable
- Task Scheduler is preferred when it installs cleanly on the machine
- broker install state must be recorded in `broker_install_state.json`

Startup install command:

```powershell
powershell -ExecutionPolicy Bypass -File <workspace-root>\ai_rules\install_startup_broker.ps1
```

Scheduled task install command:

```powershell
powershell -ExecutionPolicy Bypass -File <workspace-root>\ai_rules\install_cli_broker_task.ps1
```

## Health and doctor policy
The doctor command is the required health gate.

Base check:

```powershell
python <workspace-root>\ai_rules\doctor_ai_broker.py
```

Machine-readable health and log audit:

```powershell
python <workspace-root>\ai_rules\doctor_ai_broker.py --audit-logs --json
```

Provider smoke test:

```powershell
python <workspace-root>\ai_rules\doctor_ai_broker.py --provider-smoke gemini
```

Required healthy checks:
- autostart wiring
- broker runtime directories
- SQLite reachability
- archive writability
- env loading
- provider executable presence
- recent session log audit

## Normal broker operations
Queue a routed task:

```powershell
python <workspace-root>\ai_rules\enqueue_cli_task.py --project-root "<workspace-root>\businesses\mna\projects\marketing_team" --role "social-media-specialist" --request "Build a 3-post LinkedIn campaign for MNA around nurse retention." --wait
```

Run one worker pass manually:

```powershell
python <workspace-root>\ai_rules\cli_broker_worker.py --once
```

Run one mock verification pass without submission:

```powershell
python <workspace-root>\ai_rules\cli_broker_worker.py --once --mock-output "Mock broker output for verification." --skip-submit
```

## Codex auto-submit operations
Dry-run the latest stale session:

```powershell
python <workspace-root>\ai_rules\auto_submit_codex_sessions.py --latest --dry-run
```

Dry-run for the current workdir:

```powershell
python <workspace-root>\ai_rules\auto_submit_codex_sessions.py --latest --current-workdir --dry-run
```

Submit all newly eligible stale sessions:

```powershell
python <workspace-root>\ai_rules\auto_submit_codex_sessions.py --all
```

Policy notes:
- the first unattended `--all` run establishes the cutoff and does not backfill older sessions
- later runs only pick up newer stale sessions
- the audit should be used to catch gaps, not manual guesswork

## Manual fallback operations
Use manual submit when the AI client cannot call local tools directly.

```powershell
python <workspace-root>\ai_rules\manual_submit.py
```

Manual fallback rules:
- use the same normalized schema as the automatic pipeline
- do not create ad hoc records outside the pipeline
- confirm the result reaches SQLite and Notion

## Retry operations
Retry a specific session:

```powershell
python <workspace-root>\ai_rules\retry_session.py --session-id SESSION_ID
```

Retry all retry-needed sessions:

```powershell
python <workspace-root>\ai_rules\retry_session.py --status retry-needed
```

Retry policy:
- use the normalized payload path from SQLite
- do not rebuild payloads by hand if the normalized payload already exists
- clear retry-needed sessions before claiming the system is fully healthy

## Backfill operations
Use broker backfill to ingest result files that exist in broker output but never made it into session logging.

Dry-run:

```powershell
python <workspace-root>\ai_rules\backfill_broker_logs.py --dry-run
```

Live run:

```powershell
python <workspace-root>\ai_rules\backfill_broker_logs.py
```

Failed-only backfill:

```powershell
python <workspace-root>\ai_rules\backfill_broker_logs.py --failed-only
```

Backfill rules:
- ignore mock or skip-submit broker outputs
- ignore result files already represented in SQLite as submitted
- treat backfill as a recovery tool, not the normal path

## Audit policy
The audit is the enforcement layer behind the claim that meaningful sessions get logged.

The audit must detect:
- missing stale Codex sessions with no submitted log
- retry-needed or partial SQLite records
- broker completion records with missing logging status
- failed broker result files with no session record

The claim is operationally true only when:
- the doctor is `healthy`
- the session log audit is `ok`
- no recent retry-needed or partial sessions remain unresolved

## Failure handling rules
### If Notion fails first
- archive locally
- record the failure in SQLite
- mark the session `retry-needed`
- keep the normalized payload path for replay

### If Google Docs fails after Notion succeeds
- preserve the Notion page ID
- mark the session `partial` or `retry-needed` as appropriate
- retry from the normalized payload

### If provider execution fails
- keep the broker result file
- submit the failure as a meaningful troubleshooting session when possible
- use backfill if the first logging attempt was skipped or failed

### If broker processing stalls
- allow stale-processing recovery to re-queue the task
- inspect `processing`, `done`, `failed`, and broker logs before manual deletion

## Operational verification checklist
Use this checklist after setup changes or repairs:
1. run `install_ai_broker.ps1` or the targeted installer you changed
2. run `setup_gemini_broker.ps1` if provider auth changed
3. run `doctor_ai_broker.py --audit-logs --json`
4. run one real brokered task
5. confirm the task result logs to Notion, Google Docs, archive, and SQLite
6. clear any retry-needed records
7. confirm the doctor returns `healthy`

## Uninstall procedure
Remove broker wiring with:

```powershell
powershell -ExecutionPolicy Bypass -File <workspace-root>\ai_rules\uninstall_ai_broker.ps1
```

Only remove broker-owned runtime data through the uninstall script. Do not manually delete shared archive content unless the deletion scope has been verified.

## Current truth standard
Use this wording for docs and public descriptions:
- routed multi-model execution exists
- brokered provider handoff works live
- meaningful sessions are logged through the pipeline
- health is verified with install, setup, doctor, retry, and audit tooling

Avoid stronger wording unless it is still true under audit.
