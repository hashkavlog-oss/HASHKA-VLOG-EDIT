#!/usr/bin/env bash
# Claude Code on the web: paste this into the environment's "Setup script"
# so every new cloud session is ready (deps + Whisper model cached per session).
set -e
cd /home/user/HASHKA-VLOG-EDIT 2>/dev/null || cd "$(dirname "$0")"
python3 -m pip install -q -r requirements.txt
(cd remotion && npm ci --silent)
mkdir -p .claude && [ -f .claude/settings.json ] || cp config/claude-settings.example.json .claude/settings.json
