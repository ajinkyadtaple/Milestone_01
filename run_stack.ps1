# Start Phase 3 + Phase 4 via run_local.py (handles port conflicts)
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

Write-Host "Installing dependencies (if needed)..." -ForegroundColor DarkGray
pip install -q -r Phase3\requirements.txt 2>$null
pip install -q -r Phase4\requirements.txt 2>$null

python run_local.py --test
