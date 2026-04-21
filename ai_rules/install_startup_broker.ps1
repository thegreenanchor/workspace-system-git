param(
    [string]$StartupFileName = "AI CLI Broker.vbs"
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$workerCommandPath = Join-Path $scriptRoot "auto_cli_broker_worker.cmd"
$installStatePath = Join-Path $scriptRoot "broker_install_state.json"

if (-not (Test-Path $workerCommandPath)) {
    throw "Broker worker file not found: $workerCommandPath"
}

$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
if (-not (Test-Path $startupDir)) {
    throw "Startup folder not found: $startupDir"
}

$startupFilePath = Join-Path $startupDir $StartupFileName
$escapedWorkerCommandPath = $workerCommandPath.Replace('"', '""')
$vbsContent = @"
Set shell = CreateObject("WScript.Shell")
workerCmd = Chr(34) & "$escapedWorkerCommandPath" & Chr(34)
shell.Run shell.ExpandEnvironmentStrings("%ComSpec%") & " /c " & workerCmd, 0, False
"@

Set-Content -LiteralPath $startupFilePath -Value $vbsContent -Encoding ASCII

$installState = @{}
if (Test-Path $installStatePath) {
    try {
        $installState = Get-Content -Raw $installStatePath | ConvertFrom-Json -AsHashtable
    } catch {
        $installState = @{}
    }
}
$installState["startup_launcher_path"] = $startupFilePath
$installState["startup_launcher_installed_at"] = [DateTime]::UtcNow.ToString("o")
$installState | ConvertTo-Json | Set-Content -LiteralPath $installStatePath -Encoding UTF8

Write-Output "startup-installed: $startupFilePath"
