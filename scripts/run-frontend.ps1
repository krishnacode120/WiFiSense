$ErrorActionPreference = "Stop"
$projectRoot = Split-Path $PSScriptRoot -Parent
$nodeDirectory = Split-Path (Get-Command node.exe).Source -Parent
$npmPath = Join-Path $nodeDirectory "npm.cmd"
if (-not (Test-Path -LiteralPath $npmPath)) { throw "Install Node.js with its bundled npm." }
Push-Location (Join-Path $projectRoot "frontend")
try { & $npmPath run dev }
finally { Pop-Location }
