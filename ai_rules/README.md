# AI Rules Tooling

Local tooling for:
- session submission
- manual fallback submission
- retry
- project-root preflight
- managed rule sync

Open `site/index.html` in a browser for a visual overview of the broker, routing model, managed rules, and current role map.

## Setup

1. Install dependencies from `requirements.txt`.
2. Copy `.env.example` to `.env`.
3. Fill in:
   - `NOTION_TOKEN`
   - `NOTION_VERSION`
   - `GOOGLE_OAUTH_CLIENT_FILE`
   - `GOOGLE_OAUTH_TOKEN_FILE`
4. Fill in `config.yaml`:
   - Notion database ID
   - Google Doc IDs
   - local archive root
   - Drive backup archive root

Primary local runtime paths:
- Secrets: `<workspace-root>\secrets\ai_rules\`
- Session-log archive: `<workspace-root>\archive\session-logs\`
- Drive backup archive: `<drive-backup-root>\Archive\shared\session-logs\`

## Commands

```powershell
powershell -ExecutionPolicy Bypass -File .\install_ai_broker.ps1
python .\doctor_ai_broker.py
python .\doctor_ai_broker.py --provider-smoke gemini
powershell -ExecutionPolicy Bypass -File .\setup_gemini_broker.ps1
powershell -ExecutionPolicy Bypass -File .\uninstall_ai_broker.ps1
python submit_session.py --payload-file .\samples\example-session.json
python manual_submit.py
python retry_session.py --status retry-needed
python auto_submit_codex_sessions.py --latest --dry-run
python auto_submit_codex_sessions.py --latest --current-workdir --dry-run
python auto_submit_codex_sessions.py --all
python enqueue_cli_task.py --project-root "..\businesses\mna\projects\marketing_team" --role "social-media-specialist" --request "Build a 3-post LinkedIn campaign for MNA around nurse retention." --wait
python cli_broker_worker.py --once
python cli_broker_worker.py --once --mock-output "Mock broker output for verification." --skip-submit
powershell -ExecutionPolicy Bypass -File .\install_startup_broker.ps1
powershell -ExecutionPolicy Bypass -File .\install_cli_broker_task.ps1
powershell -ExecutionPolicy Bypass -File .\install_auto_submit_codex_task.ps1
python preflight_rules.py --cwd "..\businesses\mna\projects\marketing_team"
python sync_rules.py
```

## Notes

- `submit_session.py` writes to Notion first, then Google Docs.
- `submit_session.py` archives locally first and mirrors the archive to the configured Drive backup roots on a best-effort basis.
- `manual_submit.py` is for pasted JSON fallback from weaker clients.
- `auto_submit_codex_sessions.py` reads local `.codex/sessions`, builds payloads automatically, and submits closed sessions without hand-written JSON.
- The first unattended `auto_submit_codex_sessions.py --all` run bootstraps a cutoff file and does not backfill old sessions. Later runs only pick up newer stale sessions.
- `enqueue_cli_task.py` writes broker tasks into the shared queue and can wait for completion.
- `cli_broker_worker.py` processes queued tasks, invokes Gemini or Claude headlessly, and can feed results into the existing session log pipeline.
- `install_ai_broker.ps1` is the one-command installer. It prepares runtime directories, installs the Startup autostart path, optionally attempts Task Scheduler registration, optionally runs Gemini setup, and can run the broker doctor.
- `doctor_ai_broker.py` reports whether the broker is `healthy`, `degraded`, or `broken`, with checks for autostart wiring, queue dirs, SQLite, archive writability, env vars, and provider executables.
- `setup_gemini_broker.ps1` verifies the Gemini wrapper, ensures its home dirs exist, and can run an interactive smoke test that caches auth for broker use.
- `uninstall_ai_broker.ps1` removes broker autostart wiring and can optionally delete broker-owned runtime data.
- `install_startup_broker.ps1` installs the verified autostart path on this machine by writing `AI CLI Broker.vbs` into the current-user Startup folder.
- `install_cli_broker_task.ps1` is optional. It tries to register the broker as a Windows scheduled task, but some Windows setups reject that path without higher privileges.
- Provider routing defaults live in `global_cli_policy.yaml`, with optional project overrides via `AI_ROUTING.yaml`.
- `sync_rules.py` is implemented but not auto-run against your instruction files.
- Google Docs auth now uses desktop OAuth and will open a browser consent flow on first use.
- Live verification completed: brokered Gemini routing worked, and `submit_session.py` successfully wrote a smoke-test session to Notion, Google Docs, the local archive, and SQLite.

## WSL Media Ingest

This workflow is intended to run from Kali in WSL and writes downloaded media to the Windows-mounted workspace at:

- `../raw-media-downloads`

Long-form operating guide:

- `WSL_MEDIA_INGEST_SOP.md`

Create the Linux-side config files:

```bash
mkdir -p ~/.config/ai-rules-media-ingest
mkdir -p ~/.config/yt-dlp
cp ./ai_rules/media_ingest.env.example ~/.config/ai-rules-media-ingest/.env
```

Minimal `yt-dlp` base config:

```bash
cat > ~/.config/yt-dlp/config <<'EOF'
-P ./raw-media-downloads
-o %(title)s.%(ext)s
EOF
```

Run from Kali:

```bash
python3 ./ai_rules/media_ingest.py "REAL_SUPPORTED_URL_HERE"
```

Audio-only mode:

```bash
python3 ./ai_rules/media_ingest.py "REAL_SUPPORTED_URL_HERE" --audio-only
```

Dry-run mode skips Notion writes and prints the computed payload:

```bash
python3 ./ai_rules/media_ingest.py "REAL_SUPPORTED_URL_HERE" --dry-run
```

The first live run will create a new Notion database under `MEDIA_INGEST_PARENT_PAGE_ID` if `MEDIA_INGEST_DATABASE_ID` and `MEDIA_INGEST_DATA_SOURCE_ID` are blank. After that, the script stores the resolved IDs in:

- `~/.config/ai-rules-media-ingest/state.json`

Maintenance commands from Kali:

```bash
python3 ./ai_rules/media_maintenance.py
python3 ./ai_rules/media_maintenance.py --check-notion
python3 ./ai_rules/media_maintenance.py --apply
```

`media_maintenance.py` defaults to report-only. Use `--apply` to delete older duplicate local files. `--check-notion` reports duplicate Notion pages for the same source key but does not delete them.
