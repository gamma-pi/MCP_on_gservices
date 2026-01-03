# MCP Google Services Server

A Python-based Model Context Protocol (MCP) server that connects your local LLM to Google Calendar and Gmail.

## What is this?

This MCP server lets your local LLM (like Ollama, Claude via Continue.dev, etc.) interact with your Google Calendar and Gmail. Your LLM can:

- 📅 List, create, and manage calendar events
- 📧 Read, send, and search emails
- 🔒 All data stays local - no cloud hosting needed

## Features

### Google Calendar
- List upcoming events
- Create new events with attendees
- View event details

### Gmail
- List recent messages
- Read full email content
- Send emails
- Search emails with Gmail query syntax

## Prerequisites

- Python 3.8 or higher
- A Google account
- PyCharm (recommended) or any Python IDE

## Setup

### 1. Get Google API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select existing)
3. Enable these APIs:
   - Google Calendar API
   - Gmail API
4. Configure OAuth consent screen:
   - Choose "External"
   - Add your email as a test user
5. Create OAuth 2.0 credentials:
   - Type: Desktop app
   - Download the `credentials.json` file
6. Place `credentials.json` in your project root directory

**Detailed guide**: See the "Step-by-Step: Getting Google Credentials" artifact

### 2. Set Up Virtual Environment

#### In PyCharm:
1. Open the project in PyCharm
2. Go to **File > Settings > Project > Python Interpreter**
3. Click **Add Interpreter > Add Local Interpreter**
4. Select **Virtualenv Environment** tab
5. Choose **New environment**
6. Change location to end with `/mcp` (e.g., `/home/user/mcp-google-services/mcp`)
7. Select Python 3.8+ as base interpreter
8. Click **OK**

#### Or via Terminal:
```bash
# Create virtual environment
python3 -m venv mcp

# Activate it
source mcp/bin/activate  # Linux/Mac
mcp\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Authenticate with Google

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

Or manually:
```bash
# Activate your venv first
source mcp/bin/activate

# Run the server once to trigger OAuth flow
python src/server.py
```

A browser window will open. Sign in and grant permissions. This creates `token.pickle` which stores your authenticated session.

### 4. Connect to Your LLM

Add this to your MCP client configuration:

#### For Ollama + Open WebUI:
1. Open Open WebUI at http://localhost:3000
2. Go to **Admin Settings > Connections > MCP Servers**
3. Add new server:
   - **Name**: `google-services`
   - **Command**: `python3`
   - **Arguments**: `/absolute/path/to/mcp-google-services/src/server.py`

#### For Continue.dev (VSCode):
Edit `~/.continue/config.json`:
```json
{
  "mcpServers": {
    "google-services": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp-google-services/src/server.py"]
    }
  }
}
```

#### For Cline (VSCode):
Add in Cline settings under MCP Servers:
- **Command**: `python3`
- **Args**: `/absolute/path/to/mcp-google-services/src/server.py`

**Important**: Use the FULL absolute path to `server.py`, not a relative path!

To get your full path:
```bash
cd /path/to/mcp-google-services
pwd
# Returns something like: /home/username/mcp-google-services
# Use: /home/username/mcp-google-services/src/server.py
```

## Usage

Once connected, you can ask your LLM things like:

- "What's on my calendar tomorrow?"
- "Create a meeting for next Monday at 2pm titled 'Project Review'"
- "Show me my recent emails"
- "Send an email to john@example.com about the meeting"
- "Search my emails for messages from Sarah sent last week"

The LLM will automatically use the MCP tools to interact with your Google services.

## Available Tools

Your LLM can use these tools:

| Tool | Description |
|------|-------------|
| `calendar_list_events` | List upcoming calendar events |
| `calendar_create_event` | Create a new calendar event |
| `gmail_list_messages` | List recent Gmail messages |
| `gmail_read_message` | Read a specific email |
| `gmail_send_message` | Send an email |

## Project Structure

```
mcp-google-services/
├── mcp/                    # Virtual environment (created by you)
├── src/
│   └── server.py          # Main MCP server
├── requirements.txt        # Python dependencies
├── setup.sh               # Setup helper script
├── .gitignore             # Git ignore rules
├── credentials.json       # OAuth credentials (YOU provide)
├── token.pickle           # Generated after authentication
└── README.md              # This file
```

## Security

⚠️ **NEVER commit these files to git:**
- `credentials.json` - Your OAuth credentials
- `token.pickle` - Your access token

The `.gitignore` file is configured to prevent this, but always double-check before pushing to a repository.

## How It Works

MCP servers run **locally** on your machine:

1. Your LLM client (Ollama, Continue.dev, etc.) spawns the Python process
2. They communicate via stdin/stdout (no network, no ports)
3. The server authenticates with Google using your credentials
4. Your LLM can now call tools to interact with Calendar/Gmail
5. All data stays on your local machine

**No cloud deployment needed!**

## Troubleshooting

### "Module 'mcp' not found"
```bash
# Make sure venv is activated
source mcp/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### "credentials.json not found"
Make sure you downloaded it from Google Cloud Console and placed it in the project root directory.

### "Permission denied" errors
```bash
chmod +x setup.sh
chmod +x src/server.py
```

### Authentication issues
Delete `token.pickle` and run authentication again:
```bash
rm token.pickle
python src/server.py
```

### Can't find full path
```bash
# Linux/Mac
cd /path/to/mcp-google-services
pwd

# Windows
cd C:\path\to\mcp-google-services
cd
```

### LLM can't connect to MCP server
- Verify you're using the FULL absolute path to `server.py`
- Make sure the virtual environment has all dependencies installed
- Check that `credentials.json` and `token.pickle` exist
- Try restarting your LLM client

## Docker (Optional)

If you prefer to run via Docker:

```bash
# Build image
docker build -t mcp-google .

# Run (mount credentials as volumes)
docker run -i --rm \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/token.pickle:/app/token.pickle \
  mcp-google
```

## Contributing

This is an MVP. Suggestions and improvements welcome!

Possible enhancements:
- Support for multiple calendars
- Email attachments
- Calendar event updates/deletions
- Gmail labels and filters
- Google Drive integration

## License

MIT

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Verify all setup steps were completed
3. Check that your Google Cloud project has the required APIs enabled
4. Make sure you're added as a test user in the OAuth consent screen

## Links

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [Google Calendar API](https://developers.google.com/calendar)
- [Gmail API](https://developers.google.com/gmail)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)