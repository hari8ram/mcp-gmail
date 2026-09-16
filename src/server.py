"""
Gmail MCP Server — server.py
Main MCP server entry point. Registers all Gmail tools and starts
the stdio transport for communication with MCP clients.

Compatible with mcp SDK v2.x (uses add_request_handler API).
"""

import asyncio
import logging
import sys

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server
from dotenv import load_dotenv

from src.gmail_client import gmail_client

# Tools
from src.tools import list_unread, get_content, search_emails, mark_read, list_labels, trash_email

load_dotenv()

# Use stderr for logging so it doesn't interfere with MCP stdio protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp-gmail")

# ─────────────────────────────────────────────────────────────────────────────
# Create MCP Server
# ─────────────────────────────────────────────────────────────────────────────

server = Server("mcp-gmail")


# ─────────────────────────────────────────────────────────────────────────────
# Register: tools/list  — tells clients what tools are available
# ─────────────────────────────────────────────────────────────────────────────

async def handle_list_tools(ctx, request: types.PaginatedRequestParams) -> types.ListToolsResult:
    return types.ListToolsResult(
        tools=[
            list_unread.get_tool_definition(),
            get_content.get_content_tool_definition(),
            get_content.get_summary_tool_definition(),
            search_emails.get_tool_definition(),
            mark_read.get_tool_definition(),
            trash_email.get_tool_definition(),
            list_labels.get_list_labels_tool_definition(),
            list_labels.get_emails_by_label_tool_definition(),
        ]
    )


server.add_request_handler(
    "tools/list",
    types.PaginatedRequestParams,
    handle_list_tools,
)


# ─────────────────────────────────────────────────────────────────────────────
# Register: tools/call  — executes a specific tool
# ─────────────────────────────────────────────────────────────────────────────

async def handle_call_tool(ctx, request: types.CallToolRequestParams) -> types.CallToolResult:
    name = request.name
    arguments = request.arguments or {}

    logger.info(f"Tool called: {name} | args: {arguments}")

    try:
        match name:
            case "list_unread_emails":
                content = await list_unread.handle(arguments)
            case "get_email_content":
                content = await get_content.handle_get_content(arguments)
            case "get_email_summary":
                content = await get_content.handle_get_summary(arguments)
            case "search_emails":
                content = await search_emails.handle(arguments)
            case "mark_as_read":
                content = await mark_read.handle(arguments)
            case "trash_emails":
                content = await trash_email.handle(arguments)
            case "list_labels":
                content = await list_labels.handle_list_labels(arguments)
            case "get_emails_by_label":
                content = await list_labels.handle_get_emails_by_label(arguments)
            case _:
                content = [
                    types.TextContent(type="text", text=f'❌ Unknown tool: "{name}"')
                ]

        return types.CallToolResult(content=content)

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=f'❌ Error executing tool "{name}": {e}',
                )
            ],
            isError=True,
        )


server.add_request_handler(
    "tools/call",
    types.CallToolRequestParams,
    handle_call_tool,
)


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    print("🔐 Gmail MCP Server — Initializing...", file=sys.stderr)

    try:
        gmail_client.initialize()
        print("✅ Gmail authentication successful", file=sys.stderr)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        print(
            "\n👉 Run:  python -m src.auth\nto complete first-time authorization.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Gmail initialization failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("🚀 Gmail MCP Server running (stdio transport)", file=sys.stderr)
    print(
        "   Tools: list_unread_emails, get_email_content, get_email_summary,\n"
        "          search_emails, mark_as_read, trash_emails, list_labels, get_emails_by_label",
        file=sys.stderr,
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
