#!/bin/bash

echo "🚀 MCP Google Services Setup"
echo "=============================="

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    echo "❌ credentials.json not found!"
    echo ""
    echo "Please follow these steps:"
    echo "1. Go to https://console.cloud.google.com"
    echo "2. Create a new project or select existing"
    echo "3. Enable Google Calendar API and Gmail API"
    echo "4. Create OAuth 2.0 credentials (Desktop app)"
    echo "5. Download the credentials.json file to this directory"
    exit 1
fi

echo "✓ Found credentials.json"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run authentication
echo ""
echo "🔐 Starting authentication flow..."
echo "A browser window will open for you to authorize the app"
python3 -c "
from src.server import get_google_creds
print('Authenticating...')
get_google_creds()
print('✓ Authentication successful!')
"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To use with your local LLM, add this to your MCP client config:"
echo ""
echo '{
  "mcpServers": {
    "google-services": {
      "command": "python3",
      "args": ["'$(pwd)'/src/server.py"]
    }
  }
}'