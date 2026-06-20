# Stop immediately if any command fails.
$ErrorActionPreference = "Stop"

# Find the main telegram-groq-agent folder.
$projectRoot = Split-Path -Parent $PSScriptRoot

# Move PowerShell into the project folder.
Set-Location $projectRoot

# Start the Telegram bot.
python -m app.telegram_bot
