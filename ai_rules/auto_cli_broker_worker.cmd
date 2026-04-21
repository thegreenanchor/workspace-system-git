@ECHO OFF
SETLOCAL
CD /D "%~dp0"
SET "PYTHON_EXE=C:\Python314\python.exe"
IF EXIST "%PYTHON_EXE%" GOTO loop
SET "PYTHON_EXE=python"
:loop
"%PYTHON_EXE%" cli_broker_worker.py --once
REM Keep the poll interval shorter than enqueue_cli_task.py's rescue-worker bootstrap window.
REM Otherwise --wait calls fall back to an in-session worker before the background broker can pick up the task.
timeout /t 2 /nobreak >NUL
GOTO loop
