param(
    [string]$TaskName = "Auto Submit Codex Sessions",
    [int]$IntervalMinutes = 10
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$hiddenLauncher = Join-Path $scriptRoot "start_auto_submit_codex_hidden.vbs"

if (-not (Test-Path $hiddenLauncher)) {
    throw "Hidden launcher file not found: $hiddenLauncher"
}

$taskCommand = "wscript.exe `"$hiddenLauncher`""
schtasks /Create /TN $TaskName /SC MINUTE /MO $IntervalMinutes /TR $taskCommand /F | Out-Null
Write-Output "scheduled: $TaskName"
