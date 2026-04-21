param(
    [switch]$RemoveRuntimeData
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$startupFilePath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup\AI CLI Broker.vbs"
$taskName = "AI CLI Broker"
$configPath = Join-Path $scriptRoot "config.yaml"

if (Test-Path $startupFilePath) {
    Remove-Item -LiteralPath $startupFilePath -Force
    Write-Output "startup-removed: $startupFilePath"
} else {
    Write-Output "startup-missing: $startupFilePath"
}

& schtasks /Delete /TN $taskName /F 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Output "scheduled-task-removed: $taskName"
} else {
    Write-Output "scheduled-task-missing-or-blocked: $taskName"
}

if ($RemoveRuntimeData) {
    $config = Get-Content -Raw $configPath | ConvertFrom-Yaml
    $runtimeTargets = @(
        $config.broker.root_dir,
        $config.sqlite.path,
        (Join-Path $scriptRoot "temp_payloads")
    ) | Select-Object -Unique
    foreach ($runtimeTarget in $runtimeTargets) {
        if (Test-Path $runtimeTarget) {
            Remove-Item -LiteralPath $runtimeTarget -Recurse -Force
            Write-Output "runtime-removed: $runtimeTarget"
        }
    }
}
