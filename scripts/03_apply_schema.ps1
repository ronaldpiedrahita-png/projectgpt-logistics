$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot

& "$projectRoot\.venv\Scripts\Activate.ps1"
python -m db.setup_database
