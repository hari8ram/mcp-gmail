"""
Tool: list_unread_emails
Lists all unread emails from the Gmail inbox.
"""

import mcp.types as types
from src.gmail_client import gmail_client, EmailSummary


def get_tool_definition() -> types.Tool:
    return types.Tool(
        name="list_unread_emails",
        description=(
            "Lists all unread emails in your Gmail inbox. "
            "Returns subject, sender, date, ID, and a short preview for each email. "
            "Use this first to see what's waiting to be read."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "number",
                    "description": "Maximum number of unread emails to return (default: 20, max: 100)",
                    "default": 20,
                }
            },
            "required": [],
        },
    )


async def handle(arguments: dict) -> list[types.TextContent]:
    max_results = min(int(arguments.get("max_results", 20)), 100)
    emails = gmail_client.list_unread_emails(max_results)

    if not emails:
        return [
            types.TextContent(
                type="text",
                text="✅ No unread emails found. Your inbox is clean!",
            )
        ]

    return [
        types.TextContent(
            type="text",
            text=format_email_list(emails, f"Unread Emails"),
        )
    ]


def format_email_list(emails: list[EmailSummary], title: str) -> str:
    lines = [
        f"📬 {title} ({len(emails)} found)",
        "─" * 60,
        "",
    ]
    for i, email in enumerate(emails, start=1):
        lines.append(email.format(index=i))
    return "\n".join(lines)
