$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot

& "$projectRoot\.venv\Scripts\Activate.ps1"

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
