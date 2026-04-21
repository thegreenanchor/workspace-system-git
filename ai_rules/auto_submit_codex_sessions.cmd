@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
python "%SCRIPT_DIR%auto_submit_codex_sessions.py" --all
