"""
Tools: get_email_content, get_email_summary
Fetch full body or metadata for a specific email by ID.
"""

import mcp.types as types
from src.gmail_client import gmail_client


def get_content_tool_definition() -> types.Tool:
    return types.Tool(
        name="get_email_content",
        description=(
            "Fetches the complete content of an email by its ID, including the full body text, "
            "sender details, and attachment information. Use this after list_unread_emails or "
            "search_emails to read the full content of a specific email."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "email_id": {
                    "type": "string",
                    "description": "The Gmail message ID (obtained from list_unread_emails or search_emails)",
                }
            },
            "required": ["email_id"],
        },
    )


def get_summary_tool_definition() -> types.Tool:
    return types.Tool(
        name="get_email_summary",
        description=(
            "Gets lightweight metadata (subject, from, date, snippet) for a specific email by ID, "
            "without fetching the full body. Faster than get_email_content when you only need header info."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "email_id": {
                    "type": "string",
                    "description": "The Gmail message ID",
                }
            },
            "required": ["email_id"],
        },
    )


async def handle_get_content(arguments: dict) -> list[types.TextContent]:
    email_id = arguments.get("email_id", "").strip()
    if not email_id:
        return [types.TextContent(type="text", text="❌ Error: email_id is required.")]

    email = gmail_client.get_email_content(email_id)
    if not email:
        return [
            types.TextContent(
                type="text", text=f"❌ Email not found with ID: {email_id}"
            )
        ]

    status = "🔴 UNREAD" if email.is_unread else "✅ READ"
    lines = [
        "📧 Email Content",
        "─" * 60,
        f"Subject  : {email.subject}",
        f"From     : {email.sender}",
        f"To       : {email.to}",
        f"Date     : {email.date}",
        f"ID       : {email.id}",
        f"Thread   : {email.thread_id}",
        f"Status   : {status}",
        f"Labels   : {', '.join(email.labels) or 'none'}",
        "",
        "─" * 60,
        "📄 Body",
        "─" * 60,
        "",
    ]

    if email.body_text:
        lines.append(email.body_text)
    elif email.body_html:
        lines.append(gmail_client.strip_html(email.body_html))
    else:
        lines.append("(No body content found)")

    if email.attachments:
        lines += [
            "",
            "─" * 60,
            f"📎 Attachments ({len(email.attachments)})",
            "─" * 60,
        ]
        for i, att in enumerate(email.attachments, start=1):
            size = _format_bytes(att.get("size", 0))
            lines.append(f"{i}. {att['filename']} ({att['mimeType']}, {size})")

    return [types.TextContent(type="text", text="\n".join(lines))]


async def handle_get_summary(arguments: dict) -> list[types.TextContent]:
    email_id = arguments.get("email_id", "").strip()
    if not email_id:
        return [types.TextContent(type="text", text="❌ Error: email_id is required.")]

    email = gmail_client.get_email_summary(email_id)
    if not email:
        return [
            types.TextContent(
                type="text", text=f"❌ Email not found with ID: {email_id}"
            )
        ]

    status = "🔴 UNREAD" if email.is_unread else "✅ READ"
    lines = [
        "📧 Email Summary",
        "─" * 60,
        f"Subject  : {email.subject}",
        f"From     : {email.sender}",
        f"To       : {email.to}",
        f"Date     : {email.date}",
        f"ID       : {email.id}",
        f"Status   : {status}",
        f"Labels   : {', '.join(email.labels) or 'none'}",
        "",
        f"Preview  : {email.snippet}",
    ]

    return [types.TextContent(type="text", text="\n".join(lines))]


def _format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
