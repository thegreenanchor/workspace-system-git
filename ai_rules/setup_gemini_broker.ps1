param(
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$geminiWrapperPath = Join-Path $scriptRoot "gemini-broker.cmd"
$geminiHomePath = Join-Path $scriptRoot "gemini-home"
$geminiDotDirPath = Join-Path $geminiHomePath ".gemini"

if (-not (Test-Path $geminiWrapperPath)) {
    throw "Gemini broker wrapper not found: $geminiWrapperPath"
}

New-Item -ItemType Directory -Path $geminiHomePath -Force | Out-Null
New-Item -ItemType Directory -Path $geminiDotDirPath -Force | Out-Null

$helpOutput = & $geminiWrapperPath --help 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Gemini wrapper failed its help check.`n$helpOutput"
}

Write-Output "gemini-wrapper-ok: $geminiWrapperPath"
Write-Output "gemini-home-ok: $geminiHomePath"

if ($SkipSmokeTest) {
    Write-Output "gemini-smoke-skipped"
    return
}

$authOutput = cmd.exe /c """$geminiWrapperPath"" ""Authentication smoke test. Reply with exactly GEMINI_SETUP_OK."""
if ($LASTEXITCODE -ne 0) {
    throw "Gemini interactive setup failed.`n$authOutput"
}
if ($authOutput -notmatch "GEMINI_SETUP_OK") {
    throw "Gemini setup did not return the expected smoke-test reply.`n$authOutput"
}

Write-Output "gemini-smoke-ok"
