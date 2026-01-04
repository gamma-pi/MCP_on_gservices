#!/usr/bin/env python3
"""Minimal MCP server to test if Continue can connect"""
import asyncio
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Create MCP server
server = Server("test-mcp")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="test_tool",
            description="A simple test tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "test_tool":
        msg = arguments.get("message", "Hello!")
        return [TextContent(type="text", text=f"Test response: {msg}")]
    return [TextContent(type="text", text="Unknown tool")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="test-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())