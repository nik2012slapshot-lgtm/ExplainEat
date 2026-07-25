# Setup-Skript für ExplainEat
# Dieses Skript muss im Projektverzeichnis ExplainEat ausgeführt werden.
$project = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $project

if (-Not (Test-Path .venv)) {
    python -m venv .venv
}

& "$project\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Pop-Location
