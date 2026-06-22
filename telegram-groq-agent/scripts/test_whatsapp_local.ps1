# Stop immediately if any command fails.
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "WhatsApp local tests (no Meta account)" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Unit tests..." -ForegroundColor Yellow
python -m pytest tests/test_whatsapp_webhook.py tests/test_whatsapp_simulation.py -q

Write-Host ""
Write-Host "[2/3] Direct agent simulation (needs Groq keys)..." -ForegroundColor Yellow
python scripts/simulate_whatsapp.py --mode direct --message "Clinic kahan hai phase 7 mein?"

Write-Host ""
Write-Host "[3/3] Tip: For full HTTP stack test, run in two terminals:" -ForegroundColor Yellow
Write-Host "  Terminal 1: .\scripts\run_whatsapp_simulation.ps1"
Write-Host "  Terminal 2: python scripts/simulate_whatsapp.py --mode http --scenarios"
