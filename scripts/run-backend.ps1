param([ValidateSet("simulation", "system")][string]$Mode = "simulation")
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $projectRoot ".venv/Scripts/python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Create .venv and install backend/requirements.txt first. See README.md."
}
$env:WIFISENSE_MODE = $Mode
Push-Location (Join-Path $projectRoot "backend")
try { & $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8000 }
finally { Pop-Location }
