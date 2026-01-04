#!/usr/bin/env python3
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
import uvicorn
import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import base64
from email.mime.text import MIMEText

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_google_creds():
    """Get or create Google API credentials"""
    TOKEN_PATH = '/home/yiorgos/Documents/local repos/MCP-mvp/token.pickle'
    CREDS_PATH = '/home/yiorgos/Documents/local repos/MCP-mvp/credentials.json'
    
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

# Initialize services
_calendar_service = None
_gmail_service = None

def get_services():
    """Get or initialize Google services"""
    global _calendar_service, _gmail_service
    if _calendar_service is None or _gmail_service is None:
        creds = get_google_creds()
        _calendar_service = build('calendar', 'v3', credentials=creds)
        _gmail_service = build('gmail', 'v1', credentials=creds)
    return _calendar_service, _gmail_service

# FastAPI app
app = FastAPI(title="MCP Google Services")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ToolCall(BaseModel):
    name: str
    arguments: dict

class ToolResponse(BaseModel):
    result: Any
    error: Optional[str] = None

@app.get("/")
async def root():
    return {"status": "MCP Google Services HTTP Server Running"}

@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    return {
        "tools": [
            {
                "name": "calendar_list_events",
                "description": "List upcoming calendar events",
                "parameters": {
                    "max_results": {"type": "number", "default": 10}
                }
            },
            {
                "name": "calendar_create_event",
                "description": "Create a new calendar event",
                "parameters": {
                    "summary": {"type": "string", "required": True},
                    "description": {"type": "string"},
                    "start_time": {"type": "string", "required": True},
                    "end_time": {"type": "string", "required": True},
                    "attendees": {"type": "array"}
                }
            },
            {
                "name": "gmail_list_messages",
                "description": "List recent Gmail messages",
                "parameters": {
                    "max_results": {"type": "number", "default": 10},
                    "query": {"type": "string"}
                }
            },
            {
                "name": "gmail_read_message",
                "description": "Read a specific Gmail message",
                "parameters": {
                    "message_id": {"type": "string", "required": True}
                }
            },
            {
                "name": "gmail_send_message",
                "description": "Send an email via Gmail",
                "parameters": {
                    "to": {"type": "string", "required": True},
                    "subject": {"type": "string", "required": True},
                    "body": {"type": "string", "required": True}
                }
            }
        ]
    }

@app.post("/call_tool")
async def call_tool(tool_call: ToolCall) -> ToolResponse:
    """Execute an MCP tool"""
    try:
        calendar_service, gmail_service = get_services()
        name = tool_call.name
        args = tool_call.arguments
        
        if name == "calendar_list_events":
            max_results = args.get("max_results", 10)
            now = datetime.utcnow().isoformat() + 'Z'
            
            events_result = calendar_service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            formatted = [{
                'id': e.get('id'),
                'summary': e.get('summary'),
                'start': e.get('start', {}).get('dateTime', e.get('start', {}).get('date')),
                'end': e.get('end', {}).get('dateTime', e.get('end', {}).get('date'))
            } for e in events]
            
            return ToolResponse(result=formatted)
        
        elif name == "calendar_create_event":
            event = {
                'summary': args['summary'],
                'description': args.get('description', ''),
                'start': {'dateTime': args['start_time'], 'timeZone': 'UTC'},
                'end': {'dateTime': args['end_time'], 'timeZone': 'UTC'},
            }
            
            if 'attendees' in args:
                event['attendees'] = [{'email': e} for e in args['attendees']]
            
            created = calendar_service.events().insert(
                calendarId='primary', body=event
            ).execute()
            
            return ToolResponse(result={"event_link": created.get('htmlLink'), "id": created.get('id')})
        
        elif name == "gmail_list_messages":
            max_results = args.get("max_results", 10)
            query = args.get("query", "")
            
            results = gmail_service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            detailed = []
            
            for msg in messages[:max_results]:
                m = gmail_service.users().messages().get(
                    userId='me', id=msg['id'], format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = {h['name']: h['value'] for h in m.get('payload', {}).get('headers', [])}
                detailed.append({
                    'id': m['id'],
                    'from': headers.get('From'),
                    'subject': headers.get('Subject'),
                    'date': headers.get('Date')
                })
            
            return ToolResponse(result=detailed)
        
        elif name == "gmail_read_message":
            msg_id = args['message_id']
            message = gmail_service.users().messages().get(
                userId='me', id=msg_id, format='full'
            ).execute()
            
            payload = message.get('payload', {})
            headers = {h['name']: h['value'] for h in payload.get('headers', [])}
            
            body = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        break
            else:
                body = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8')
            
            return ToolResponse(result={
                'from': headers.get('From'),
                'subject': headers.get('Subject'),
                'date': headers.get('Date'),
                'body': body
            })
        
        elif name == "gmail_send_message":
            message = MIMEText(args['body'])
            message['to'] = args['to']
            message['subject'] = args['subject']
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            sent = gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            return ToolResponse(result={"message_id": sent['id']})
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {name}")
    
    except Exception as e:
        return ToolResponse(result=None, error=str(e))

if __name__ == "__main__":
    print("🚀 Starting MCP Google Services HTTP Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📋 Available endpoints:")
    print("   - GET  /         - Server status")
    print("   - GET  /tools    - List available tools")
    print("   - POST /call_tool - Execute a tool")
    uvicorn.run(app, host="0.0.0.0", port=8000)