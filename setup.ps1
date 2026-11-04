# HASHKA VLOG EDIT - Windows 11 setup
# (ASCII only: Windows PowerShell 5.1 misreads UTF-8 without BOM)
# Run in PowerShell inside this folder:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Need($cmd, $wingetId) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    Write-Host "-> installing $cmd ($wingetId)..."
    winget install -e --id $wingetId --accept-source-agreements --accept-package-agreements
    $script:restart = $true
  } else { Write-Host "OK $cmd" }
}

$restart = $false
Need git    "Git.Git"
Need ffmpeg "Gyan.FFmpeg"
Need node   "OpenJS.NodeJS.LTS"
Need python "Python.Python.3.12"

if ($restart) {
  $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
  if ((Get-Command ffmpeg -ErrorAction SilentlyContinue) -and (Get-Command node -ErrorAction SilentlyContinue) -and (Get-Command python -ErrorAction SilentlyContinue)) { $restart = $false }
}
if ($restart) {
  Write-Host ""
  Write-Host "New programs installed. CLOSE PowerShell, open it again and run this script again. (PowerShell-ee haagaad dahin neej, script-ee dahin ajilluulna uu)" -ForegroundColor Yellow
  exit 0
}

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Push-Location remotion; npm ci; Pop-Location

if (-not (Test-Path .claude\settings.json)) {
  New-Item -ItemType Directory -Force .claude | Out-Null
  Copy-Item config\claude-settings.example.json .claude\settings.json
  Write-Host "OK .claude\settings.json (token saving + permissions)"
}
Write-Host ""
Write-Host "READY! (Belen!)  Test:  python scripts\edit.py -h" -ForegroundColor Green
Write-Host "Whisper large-v3 model (~3GB) downloads on the first transcribe."
