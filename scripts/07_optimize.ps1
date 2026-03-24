$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot

& "$projectRoot\.venv\Scripts\Activate.ps1"

$today = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
$payload = @{
  date = $today
  persist_assignments = $true
} | ConvertTo-Json

$response = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/optimize-routes" -ContentType "application/json" -Body $payload
$response | ConvertTo-Json -Depth 6
