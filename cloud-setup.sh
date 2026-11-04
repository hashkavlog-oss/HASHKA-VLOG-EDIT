#!/usr/bin/env bash
# Claude Code on the web: paste into the environment's "Setup script" so new sessions are ready.
set -e
cd /home/user/HASHKA-VLOG-EDIT 2>/dev/null || cd "$(dirname "$0")"
(command -v apt-get >/dev/null && (apt-get install -y -q libegl1 libgles2 >/dev/null 2>&1 || (apt-get update -q >/dev/null && apt-get install -y -q libegl1 libgles2 >/dev/null))) || true
python3 -m pip install -q -r requirements.txt
(cd remotion && npm ci --silent)
./scripts/get_models.sh
mkdir -p .claude && [ -f .claude/settings.json ] || cp config/claude-settings.example.json .claude/settings.json
# Best Mongolian speech model (one-time ~1.6GB download + convert):
python3 scripts/edit.py setup-mn || echo "setup-mn failed; mn-small model will be used"
