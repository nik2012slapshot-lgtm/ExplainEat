# Packt den lauffaehigen ExplainEat-Code als ZIP fuer die Wettbewerbsabgabe.
# Enthaelt Code + gebaute Web-App + trainiertes Modell.
# Schliesst aus: .venv, Caches, Build-Zwischenstaende, .env (Secrets), Backups.
#
# Aufruf:
#   powershell -ExecutionPolicy Bypass -File scripts/package_submission.ps1

$ErrorActionPreference = 'Stop'
$root  = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stamp = Get-Date -Format 'yyyyMMdd'
$zipName = "ExplainEat_submission_$stamp.zip"
$zipPath = Join-Path $root $zipName
$stage = Join-Path $env:TEMP ("ExplainEat_pkg_" + (Get-Date -Format 'yyyyMMddHHmmss'))

New-Item -ItemType Directory -Force -Path $stage | Out-Null

# 'training' = grosse Trainingsbilder (fuers Ausfuehren nicht noetig)
$excludeDirs  = @('.venv','node_modules','.dart_tool','__pycache__','.git','yolo_runs','ephemeral','.pytest_cache','training')
# *.dill = Flutter-Build-Caches; food_classifier.pth = ungenutztes 42MB-Altmodell
$excludeFiles = @('.env','*.pyc','*.pyo','*.backup*.json','*.dill','food_classifier.pth','ExplainEat_submission_*.zip')

$rcArgs = @($root, $stage, '/E','/NFL','/NDL','/NJH','/NJS','/NP') + '/XD' + $excludeDirs + '/XF' + $excludeFiles
& robocopy @rcArgs | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy fehlgeschlagen (Code $LASTEXITCODE)" }

# vorhandenes ZIP im Stage entfernen (falls frueher erzeugt)
Get-ChildItem -Path $stage -Filter 'ExplainEat_submission_*.zip' -ErrorAction SilentlyContinue | Remove-Item -Force

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zipPath -Force
Remove-Item -Recurse -Force $stage

$sizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
Write-Host "OK: $zipName ($sizeMB MB) erstellt in $root"
Write-Host "Inhalt: Backend, explain_eat/, flutter_app (inkl. build/web), scripts/, tests/, submission/, README, requirements.txt, .env.example"
