# Stop immediately if any command fails.
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "Starting WhatsApp webhook in SIMULATION mode (no Meta credentials needed)..." -ForegroundColor Cyan
$env:WHATSAPP_SIMULATION_MODE = "true"
python -m app.whatsapp_webhook
