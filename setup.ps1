# HASHKA VLOG EDIT - Windows 11 setup
# Run in PowerShell inside this folder:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Need($cmd, $wingetId) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    Write-Host "-> $cmd суулгаж байна ($wingetId)..."
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
  Write-Host ""
  Write-Host "Шинэ програм суулаа. PowerShell-ээ ХААГААД дахин нээж, энэ скриптийг дахин ажиллуулна уу." -ForegroundColor Yellow
  exit 0
}

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Push-Location remotion; npm ci; Pop-Location

if (-not (Test-Path .claude\settings.json)) {
  New-Item -ItemType Directory -Force .claude | Out-Null
  Copy-Item config\claude-settings.example.json .claude\settings.json
  Write-Host "OK .claude\settings.json (токен хэмнэлт + зөвшөөрөл)"
}
Write-Host ""
Write-Host "Бэлэн! Турших:  python scripts\edit.py -h" -ForegroundColor Green
Write-Host "Whisper large-v3 модель анхны transcribe үед ~3GB татагдана."
