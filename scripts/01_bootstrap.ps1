$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

New-Item -ItemType Directory -Force api,db,ml,optimizer,simulator,scripts,artifacts,tests,.github,.github\workflows | Out-Null

if (-not (Test-Path ".git")) {
  git init
}

Write-Host "Bootstrap completado."
