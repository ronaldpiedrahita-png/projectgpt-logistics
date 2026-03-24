$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot

& "$projectRoot\.venv\Scripts\Activate.ps1"

python -m simulator.generate_orders --days 180 --rows 60000
python -m simulator.generate_gps --days 180 --rows 300000
python -m simulator.build_deliveries
