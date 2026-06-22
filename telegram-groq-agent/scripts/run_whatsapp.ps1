# Stop immediately if any command fails.
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

python -m app.whatsapp_webhook
