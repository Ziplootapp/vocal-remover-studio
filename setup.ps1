$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition }
if ($ScriptDir) { Set-Location $ScriptDir }

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " ziploot.app - 1-Click AI Vocal Separator Studio Setup" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
python -m pip install -r requirements.txt
Start-Process "http://localhost:5001"
python app.py
