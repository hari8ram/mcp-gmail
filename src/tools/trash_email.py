"""
Tool: trash_emails
Moves one or more emails to the Trash.
"""

import mcp.types as types
from src.gmail_client import gmail_client


def get_tool_definition() -> types.Tool:
    return types.Tool(
        name="trash_emails",
        description=(
            "Moves one or more Gmail emails to the Trash. "
            "Accepts a single email ID or a comma-separated list of IDs."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "email_ids": {
                    "type": "string",
                    "description": (
                        "Single email ID or comma-separated list of IDs to move to trash "
                        "(e.g. '18abc123' or '18abc123,18def456')"
                    ),
                }
            },
            "required": ["email_ids"],
        },
    )


async def handle(arguments: dict) -> list[types.TextContent]:
    raw = arguments.get("email_ids", "").strip()
    if not raw:
        return [types.TextContent(type="text", text="❌ Error: email_ids is required.")]

    ids = [i.strip() for i in raw.split(",") if i.strip()]
    results = [(id_, gmail_client.trash_email(id_)) for id_ in ids]

    succeeded = [id_ for id_, ok in results if ok]
    failed = [id_ for id_, ok in results if not ok]

    lines = ["🗑️ Trash Emails — Results", "─" * 40]

    if succeeded:
        lines.append(f"✅ Successfully moved to trash ({len(succeeded)}):")
        for id_ in succeeded:
            lines.append(f"   • {id_}")

    if failed:
        lines.append(f"❌ Failed to trash ({len(failed)}):")
        for id_ in failed:
            lines.append(f"   • {id_}")

    return [types.TextContent(type="text", text="\n".join(lines))]
