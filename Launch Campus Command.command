#!/bin/bash
cd "$(dirname "$0")"

# Load .env
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  osascript -e 'display alert "API Key Missing" message "Add ANTHROPIC_API_KEY to the .env file in campus-command folder." as critical'
  exit 1
fi

# Install Python deps
if ! python3 -c "import flask" &>/dev/null; then
  echo "Installing Python dependencies..."
  pip3 install -r requirements.txt --break-system-packages 2>/dev/null || pip3 install -r requirements.txt
fi

# Install npm deps
if [ ! -d "node_modules" ]; then
  echo "Installing npm packages (first run — may take a minute)..."
  npm install
fi

# Clear any Electron env conflicts
unset ELECTRON_RUN_AS_NODE

# Build the app
echo "Building Campus Command..."
npm run build

# Launch Electron
echo "Launching Campus Command..."
npm run electron
