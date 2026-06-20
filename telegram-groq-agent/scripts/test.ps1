# Stop immediately if any command fails.
$ErrorActionPreference = "Stop"

# Find the main telegram-groq-agent folder.
$projectRoot = Split-Path -Parent $PSScriptRoot

# Move PowerShell into the project folder.
Set-Location $projectRoot

# Run unit tests.
python -m unittest discover -s tests

# Check that all Python files can compile.
python -m compileall app tests
