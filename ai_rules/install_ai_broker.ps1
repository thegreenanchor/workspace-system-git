param(
    [switch]$SkipScheduledTask,
    [switch]$SkipGeminiSetup,
    [switch]$SkipDoctor
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $scriptRoot "config.yaml"
$startupInstallerPath = Join-Path $scriptRoot "install_startup_broker.ps1"
$taskInstallerPath = Join-Path $scriptRoot "install_cli_broker_task.ps1"
$geminiSetupPath = Join-Path $scriptRoot "setup_gemini_broker.ps1"
$doctorPath = Join-Path $scriptRoot "doctor_ai_broker.py"

if (-not (Test-Path $configPath)) {
    throw "Missing broker config: $configPath"
}

$config = Get-Content -Raw $configPath | ConvertFrom-Yaml
$runtimePaths = @(
    $config.archive.root_dir,
    (Split-Path -Parent $config.sqlite.path),
    $config.broker.root_dir
)
foreach ($runtimePath in $runtimePaths) {
    New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
}
Write-Output "runtime-dirs-ok"

& powershell -ExecutionPolicy Bypass -File $startupInstallerPath

if (-not $SkipScheduledTask) {
    try {
        & powershell -ExecutionPolicy Bypass -File $taskInstallerPath
    } catch {
        Write-Warning "Scheduled task install failed. Startup autostart remains the supported path on this machine."
    }
}

if (-not $SkipGeminiSetup) {
    & powershell -ExecutionPolicy Bypass -File $geminiSetupPath
}

if (-not $SkipDoctor) {
    python $doctorPath
}
