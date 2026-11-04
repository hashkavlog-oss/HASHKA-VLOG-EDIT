#!/usr/bin/env bash
# One-time setup. Mac: brew install ffmpeg node python  |  Ubuntu: sudo apt install ffmpeg nodejs npm python3-pip
set -e
cd "$(dirname "$0")"
for t in ffmpeg ffprobe node npm python3; do
  command -v "$t" >/dev/null || { echo "✘ $t суугаагүй байна"; exit 1; }
done
python3 -m pip install -r requirements.txt
(cd remotion && npm ci)
if [ ! -f .claude/settings.json ]; then
  mkdir -p .claude && cp config/claude-settings.example.json .claude/settings.json
  echo "✔ .claude/settings.json үүслээ (токен хэмнэлт + зөвшөөрөл)"
fi
echo "✔ Бэлэн. Турших:  python3 scripts/edit.py -h"
echo "  (Whisper large-v3 модель анхны transcribe үед ~3GB татагдана)"
