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

# Show the network URL so you can share it with other devices on the same WiFi
NETWORK_IP=$(python3 -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()" 2>/dev/null || echo "unknown")
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "  Campus Command is starting..."
echo "  Open on THIS Mac:  http://localhost:5001"
if [ "$NETWORK_IP" != "unknown" ]; then
echo "  Open on ANY device on this WiFi:"
echo "  → http://$NETWORK_IP:5001"
fi
echo "╚══════════════════════════════════════════════╝"
echo ""

# Show a macOS notification with the network address
if [ "$NETWORK_IP" != "unknown" ]; then
  osascript -e "display notification \"Browser URL: http://$NETWORK_IP:5001\" with title \"Campus Command\" subtitle \"Share this with your kid\""
fi

# Launch Electron
echo "Launching Campus Command..."
npm run electron
