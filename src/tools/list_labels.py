"""
Tools: list_labels, get_emails_by_label
List Gmail labels and fetch emails for a specific label.
"""

import mcp.types as types
from src.gmail_client import gmail_client
from src.tools.list_unread import format_email_list


def get_list_labels_tool_definition() -> types.Tool:
    return types.Tool(
        name="list_labels",
        description=(
            "Lists all Gmail labels — both system labels (INBOX, SENT, SPAM, TRASH, STARRED) "
            "and user-created custom labels. Returns label IDs and names. "
            "Use this to discover available labels for use with get_emails_by_label."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )


def get_emails_by_label_tool_definition() -> types.Tool:
    return types.Tool(
        name="get_emails_by_label",
        description=(
            "Fetches emails belonging to a specific Gmail label. "
            "Use list_labels first to get the label ID. "
            "Common IDs: INBOX, SENT, SPAM, TRASH, STARRED, IMPORTANT, DRAFT, UNREAD."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "label_id": {
                    "type": "string",
                    "description": "The label ID (e.g. 'INBOX', 'SENT', 'SPAM', or a custom label ID)",
                },
                "max_results": {
                    "type": "number",
                    "description": "Maximum number of emails to return (default: 20, max: 100)",
                    "default": 20,
                },
            },
            "required": ["label_id"],
        },
    )


async def handle_list_labels(arguments: dict) -> list[types.TextContent]:
    labels = gmail_client.list_labels()

    if not labels:
        return [types.TextContent(type="text", text="No labels found.")]

    system_labels = [l for l in labels if l.label_type == "system"]
    user_labels = [l for l in labels if l.label_type != "system"]

    lines = [f"🏷️  Gmail Labels ({len(labels)} total)", "─" * 50, ""]

    if system_labels:
        lines.append("📌 System Labels:")
        for lbl in system_labels:
            lines.append(f"   {lbl.name:<20} ID: {lbl.id}")
        lines.append("")

    if user_labels:
        lines.append("🗂️  Custom Labels:")
        for lbl in user_labels:
            lines.append(f"   {lbl.name:<20} ID: {lbl.id}")

    return [types.TextContent(type="text", text="\n".join(lines))]


async def handle_get_emails_by_label(arguments: dict) -> list[types.TextContent]:
    label_id = arguments.get("label_id", "").strip()
    if not label_id:
        return [types.TextContent(type="text", text="❌ Error: label_id is required.")]

    max_results = min(int(arguments.get("max_results", 20)), 100)
    emails = gmail_client.get_emails_by_label(label_id, max_results)

    if not emails:
        return [
            types.TextContent(
                type="text", text=f"📭 No emails found in label: {label_id}"
            )
        ]

    return [
        types.TextContent(
            type="text",
            text=format_email_list(emails, f"Emails in Label: {label_id}"),
        )
    ]
