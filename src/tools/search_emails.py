"""
Tool: search_emails
Search Gmail using Gmail's full query syntax.
"""

import mcp.types as types
from src.gmail_client import gmail_client
from src.tools.list_unread import format_email_list


def get_tool_definition() -> types.Tool:
    return types.Tool(
        name="search_emails",
        description=(
            "Search Gmail using Gmail's powerful search syntax. "
            "Examples: 'from:boss@company.com', 'subject:invoice', "
            "'is:unread after:2024/01/01', 'has:attachment', 'label:work'. "
            "Returns matching emails with subject, sender, date, and snippet."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Gmail search query. Supports: from:, to:, subject:, is:unread, "
                        "has:attachment, after:YYYY/MM/DD, before:YYYY/MM/DD, label:name, in:spam, etc."
                    ),
                },
                "max_results": {
                    "type": "number",
                    "description": "Maximum number of results to return (default: 20, max: 100)",
                    "default": 20,
                },
            },
            "required": ["query"],
        },
    )


async def handle(arguments: dict) -> list[types.TextContent]:
    query = arguments.get("query", "").strip()
    if not query:
        return [types.TextContent(type="text", text="❌ Error: query is required.")]

    max_results = min(int(arguments.get("max_results", 20)), 100)
    emails = gmail_client.search_emails(query, max_results)

    if not emails:
        return [
            types.TextContent(
                type="text",
                text=f'🔍 No emails found matching: "{query}"',
            )
        ]

    return [
        types.TextContent(
            type="text",
            text=format_email_list(emails, f'Search Results for: "{query}"'),
        )
    ]
