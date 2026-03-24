$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot

& "$projectRoot\.venv\Scripts\Activate.ps1"

python -m ml.build_features
python -m ml.train_eta_model
python -m ml.train_late_risk_model
