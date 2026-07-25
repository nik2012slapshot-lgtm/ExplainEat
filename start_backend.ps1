# Startet das ExplainEat-Backend im Projektverzeichnis
$project = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $project

& "$project\.venv\Scripts\Activate.ps1"
python backend.py

Pop-Location
