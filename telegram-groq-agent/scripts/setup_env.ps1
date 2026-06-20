# Stop immediately if any command fails.
$ErrorActionPreference = "Stop"

# Find the main telegram-groq-agent folder.
$projectRoot = Split-Path -Parent $PSScriptRoot

# This is where private keys are saved.
$envPath = Join-Path $projectRoot ".env"

# Ask user for secret keys without hard-coding them in source files.
$telegramToken = Read-Host "Telegram bot token"
$groqApiKeys = Read-Host "Groq API key(s), separated by commas"
$groqApiKey = ($groqApiKeys -split ',')[0].Trim()
$geminiApiKey = Read-Host "Gemini API key (optional fallback)"
$staffChatId = Read-Host "Staff alert chat ID (optional, press Enter to skip)"

# Build the .env file content.
$content = @"
TELEGRAM_BOT_TOKEN=$telegramToken
GROQ_API_KEY=$groqApiKey
GROQ_API_KEYS=$groqApiKeys
GROQ_MODEL=llama-3.1-8b-instant
GEMINI_API_KEY=$geminiApiKey
GEMINI_MODEL=gemini-3.5-flash
BUSINESS_PACK_DIR=../royce-aesthetics-agent
DATA_DIR=./data
STAFF_ALERT_CHAT_ID=$staffChatId
"@

# Write the .env file.
Set-Content -LiteralPath $envPath -Value $content -Encoding UTF8

# Print next-step instructions.
Write-Host "Created $envPath"
Write-Host "Run: .\scripts\run_bot.ps1"
