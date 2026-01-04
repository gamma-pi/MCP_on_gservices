# MCP Google Services - Web Chat Interface

A Python-based system that connects a local LLM (Llama 3.2) to Google Calendar and Gmail through a simple web interface.

## What is this?

This project provides a web-based chat interface where you can ask questions about your Google Calendar and Gmail. The system uses:
- **Llama 3.2** (3B) running locally via Ollama
- **HTTP API server** for Google Calendar/Gmail access
- **Web chat interface** in your browser

Your LLM can:
- 📅 List calendar events
- 📧 List and read emails
- 🔒 All data stays local - no cloud hosting needed

---

## Quick Start

### Prerequisites

- Python 3.8+
- Ollama installed
- Google account
- Brave/Chrome/Firefox browser

### Setup Steps

1. **Get Google Credentials** (see detailed guide below)
2. **Install dependencies**
3. **Authenticate with Google**
4. **Start the servers**
5. **Open chat interface**

---

## Detailed Setup

### 1. Get Google API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable these APIs:
   - Google Calendar API
   - Gmail API
4. Configure OAuth consent screen:
   - Choose "External"
   - Add your email as a test user
5. Create OAuth 2.0 credentials (Desktop app)
6. Download `credentials.json` and place in project root

### 2. Set Up Virtual Environment

```bash
cd mcp-google-services
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Authenticate with Google

```bash
source .venv/bin/activate
python src/server_http.py
```

A browser will open for OAuth. Grant permissions. This creates `token.pickle`.

Press `Ctrl+C` to stop the server after authentication.

### 4. Install Ollama and Pull Model

```bash
# Install Ollama (if not installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull Llama 3.2 3B model
ollama pull llama3.2:3b
```

---

## Running the System

You need **3 terminals** running simultaneously:

### Terminal 1: HTTP API Server

```bash
cd mcp-google-services
source .venv/bin/activate
python src/server_http.py
```

Should show:
```
🚀 Starting MCP Google Services HTTP Server...
📍 Server will be available at: http://localhost:8000
```

### Terminal 2: Ollama with CORS

```bash
OLLAMA_ORIGINS="*" ollama serve
```

Should show:
```
time=... level=INFO source=routes.go:... msg="Listening on 127.0.0.1:11434"
```

### Terminal 3: Web Server for HTML

```bash
cd mcp-google-services
python3 -m http.server 8080
```

Should show:
```
Serving HTTP on 0.0.0.0 port 8080
```

---

## Using the Chat Interface

1. Open browser to: `http://localhost:8080/chat_interface.html`

2. Ask questions like:
   - "What's on my calendar tomorrow?"
   - "Show me my recent emails"
   - "What events do I have this week?"

3. The LLM will automatically fetch data from Google and give you natural language answers

---

## Project Structure

```
mcp-google-services/
├── .venv/                     # Virtual environment
├── src/
│   ├── server.py             # MCP stdio server (not currently used)
│   └── server_http.py        # HTTP API server (⭐ main server)
├── chat_interface.html        # Web chat UI (⭐ what you use)
├── requirements.txt           # Python dependencies
├── credentials.json          # OAuth credentials (YOU provide)
├── token.pickle              # Auth token (auto-generated)
├── .gitignore                # Prevents committing secrets
└── README.md                 # This file
```

---

## How It Works

```
┌─────────────┐
│   Browser   │  You ask questions here
│ (port 8080) │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│        chat_interface.html              │
│  Determines which tool to use           │
└─────┬──────────────────────┬────────────┘
      │                      │
      │ Fetch data          │ Generate response
      ▼                      ▼
┌──────────────┐      ┌──────────────┐
│ HTTP Server  │      │   Ollama     │
│ (port 8000)  │      │ (port 11434) │
│              │      │              │
│ - Calendar   │      │ Llama 3.2 3B │
│ - Gmail      │      │              │
└──────┬───────┘      └──────────────┘
       │
       ▼
┌──────────────┐
│   Google     │
│   APIs       │
└──────────────┘
```

1. You type a question in the browser
2. JavaScript detects if it needs calendar or email data
3. Fetches data from HTTP server (port 8000)
4. HTTP server queries Google Calendar/Gmail APIs
5. Data is sent to Ollama (port 11434) with your question
6. Llama 3.2 generates a natural language response
7. Answer appears in chat

---

## Available Tools

The HTTP server exposes these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tools` | GET | List available tools |
| `/call_tool` | POST | Execute a tool |

**Available tools:**
- `calendar_list_events` - List upcoming events
- `calendar_create_event` - Create new event
- `gmail_list_messages` - List recent emails
- `gmail_read_message` - Read specific email
- `gmail_send_message` - Send an email

---

## Security

⚠️ **NEVER commit these files to git:**
- `credentials.json` - Your OAuth credentials
- `token.pickle` - Your access token

The `.gitignore` file prevents this automatically.

**Access Control:**
- HTTP server runs on `localhost` only (not accessible from internet)
- Ollama runs locally
- All data stays on your machine
- No cloud services involved

---

## Troubleshooting

### "Failed to fetch" in browser

**Check all 3 servers are running:**
```bash
curl http://localhost:8000      # HTTP server
curl http://localhost:11434     # Ollama
curl http://localhost:8080      # Web server
```

All should respond without errors.

### Ollama CORS errors

Make sure you started Ollama with:
```bash
OLLAMA_ORIGINS="*" ollama serve
```

Not just `ollama serve`

### "Model not found"

```bash
ollama list  # Check installed models
ollama pull llama3.2:3b  # Pull if missing
```

### Python errors

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Google auth errors

Delete token and re-authenticate:
```bash
rm token.pickle
python src/server_http.py
```

---

## Performance

**Expected response times on CPU:**
- Calendar queries: 3-5 seconds
- Email queries: 3-5 seconds
- Simple questions: 2-3 seconds

**With GPU (if available):**
- All queries: 1-2 seconds

---

## Making Ollama Start with CORS Automatically

To avoid typing `OLLAMA_ORIGINS="*"` every time:

```bash
# Add to ~/.bashrc
echo 'export OLLAMA_ORIGINS="*"' >> ~/.bashrc
source ~/.bashrc

# Now just use:
ollama serve
```

---

## Stopping the Servers

Press `Ctrl+C` in each terminal to stop the servers.

Or kill all at once:
```bash
pkill -f "python.*server_http"
sudo pkill ollama
pkill -f "python.*http.server"
```

---

## Future Enhancements

Possible improvements:
- ✨ Add email sending capability to chat
- ✨ Calendar event creation via chat
- ✨ Email search functionality
- ✨ Multiple calendar support
- ✨ Better conversation memory
- ✨ Voice input/output

---

## Technical Details

**Stack:**
- **Backend:** Python 3.11 + FastAPI
- **LLM:** Llama 3.2 3B via Ollama
- **APIs:** Google Calendar API, Gmail API
- **Frontend:** Vanilla JavaScript + HTML/CSS
- **No frameworks:** Pure web technologies

**Why this approach?**
- ✅ Simple setup
- ✅ Everything runs locally
- ✅ No external dependencies
- ✅ Easy to modify
- ✅ Works on modest hardware

---

## Support

**Common issues:**
1. CORS errors → Restart Ollama with `OLLAMA_ORIGINS="*"`
2. Slow responses → Normal on CPU, ~3-5 seconds
3. Can't connect → Check all 3 servers are running
4. Auth errors → Delete `token.pickle`, re-authenticate

**System Requirements:**
- 8GB RAM minimum (16GB recommended)
- Any modern CPU
- ~10GB disk space (for models)
- Internet connection (for Google APIs)

---

## License

MIT

---

## Quick Command Reference

```bash
# Start everything (use 3 separate terminals)

# Terminal 1:
cd mcp-google-services && source .venv/bin/activate && python src/server_http.py

# Terminal 2:
OLLAMA_ORIGINS="*" ollama serve

# Terminal 3:
cd mcp-google-services && python3 -m http.server 8080

# Then open browser to:
# http://localhost:8080/chat_interface.html
```