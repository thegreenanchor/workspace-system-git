param(
    [string]$TaskName = "AI CLI Broker"
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$hiddenLauncher = Join-Path $scriptRoot "start_cli_broker_hidden.vbs"
$installStatePath = Join-Path $scriptRoot "broker_install_state.json"

if (-not (Test-Path $hiddenLauncher)) {
    throw "Hidden launcher file not found: $hiddenLauncher"
}

$taskCommand = "wscript.exe `"$hiddenLauncher`""
$userName = "$env:USERDOMAIN\$env:USERNAME"

schtasks /Create /TN $TaskName /SC ONLOGON /TR $taskCommand /RL LIMITED /RU $userName /F | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to register scheduled task '$TaskName' for user '$userName'. Startup autostart remains the supported path on this machine."
    return
}

$installState = @{}
if (Test-Path $installStatePath) {
    try {
        $installState = Get-Content -Raw $installStatePath | ConvertFrom-Json -AsHashtable
    } catch {
        $installState = @{}
    }
}
$installState["scheduled_task_name"] = $TaskName
$installState["scheduled_task_installed_at"] = [DateTime]::UtcNow.ToString("o")
$installState["scheduled_task_run_as_user"] = $userName
$installState | ConvertTo-Json | Set-Content -LiteralPath $installStatePath -Encoding UTF8

Write-Output "scheduled: $TaskName"
