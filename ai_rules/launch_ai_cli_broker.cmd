@ECHO OFF
SETLOCAL
SET "SCRIPT_DIR=%~dp0"
START "" /MIN cmd /c "\"%SCRIPT_DIR%auto_cli_broker_worker.cmd\""
