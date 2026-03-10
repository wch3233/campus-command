#!/bin/bash
# Launch Campus Command — double-click to start your AI school team

cd "$(dirname "$0")"

# ── Check for Python ──────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  osascript -e 'display alert "Python 3 not found" message "Install Python 3 from python.org and try again." as critical'
  exit 1
fi

# ── Check for API key ─────────────────────────────────────────────────────────
if [ -z "$ANTHROPIC_API_KEY" ]; then
  # Try loading from .env file in this folder
  if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
  fi
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  osascript -e 'display alert "API Key Missing" message "Set ANTHROPIC_API_KEY in a .env file inside the campus-command folder, then try again." as critical'
  exit 1
fi

# ── Install dependencies if needed ────────────────────────────────────────────
if ! python3 -c "import anthropic" &>/dev/null; then
  echo "Installing dependencies..."
  pip3 install -r requirements.txt
fi

# ── Launch in Terminal ────────────────────────────────────────────────────────
clear
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   CAMPUS COMMAND — Starting up...        ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

python3 main.py --interactive
