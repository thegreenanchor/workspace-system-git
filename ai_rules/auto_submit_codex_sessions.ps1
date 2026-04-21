$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
& 'C:\Python314\python.exe' .\auto_submit_codex_sessions.py --all
