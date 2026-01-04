#!/usr/bin/env python3
import asyncio
import json
from datetime import datetime
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
import base64
from email.mime.text import MIMEText

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify'
]


def get_google_creds():
    """Get or create Google API credentials"""
    # Use absolute paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(os.path.dirname(base_dir), 'token.pickle')
    creds_path = os.path.join(os.path.dirname(base_dir), 'credentials.json')
    
    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return creds


# Global service instances (initialized lazily)
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


# Create MCP server
server = Server("google-services-mcp")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="calendar_list_events",
            description="List upcoming calendar events",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "number",
                        "description": "Max events to return",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="calendar_create_event",
            description="Create a new calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title"},
                    "description": {"type": "string", "description": "Event description"},
                    "start_time": {"type": "string", "description": "Start time (ISO 8601)"},
                    "end_time": {"type": "string", "description": "End time (ISO 8601)"},
                    "attendees": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["summary", "start_time", "end_time"]
            }
        ),
        Tool(
            name="gmail_list_messages",
            description="List recent Gmail messages",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {"type": "number", "default": 10},
                    "query": {"type": "string", "description": "Search query"}
                }
            }
        ),
        Tool(
            name="gmail_read_message",
            description="Read a specific Gmail message",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"}
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="gmail_send_message",
            description="Send an email via Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["to", "subject", "body"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        calendar_service, gmail_service = get_services()

        if name == "calendar_list_events":
            max_results = arguments.get("max_results", 10)
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

            return [TextContent(type="text", text=json.dumps(formatted, indent=2))]

        elif name == "calendar_create_event":
            event = {
                'summary': arguments['summary'],
                'description': arguments.get('description', ''),
                'start': {'dateTime': arguments['start_time'], 'timeZone': 'UTC'},
                'end': {'dateTime': arguments['end_time'], 'timeZone': 'UTC'},
            }

            if 'attendees' in arguments:
                event['attendees'] = [{'email': e} for e in arguments['attendees']]

            created = calendar_service.events().insert(
                calendarId='primary', body=event
            ).execute()

            return [TextContent(type="text", text=f"Event created: {created.get('htmlLink')}")]

        elif name == "gmail_list_messages":
            max_results = arguments.get("max_results", 10)
            query = arguments.get("query", "")

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

            return [TextContent(type="text", text=json.dumps(detailed, indent=2))]

        elif name == "gmail_read_message":
            msg_id = arguments['message_id']
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

            return [TextContent(type="text", text=json.dumps({
                'from': headers.get('From'),
                'subject': headers.get('Subject'),
                'date': headers.get('Date'),
                'body': body
            }, indent=2))]

        elif name == "gmail_send_message":
            message = MIMEText(arguments['body'])
            message['to'] = arguments['to']
            message['subject'] = arguments['subject']

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            sent = gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            return [TextContent(type="text", text=f"Message sent: {sent['id']}")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="google-services-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())