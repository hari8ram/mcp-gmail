"""
Tool: mark_as_read
Marks one or more emails as read (removes the UNREAD label).
"""

import mcp.types as types
from src.gmail_client import gmail_client


def get_tool_definition() -> types.Tool:
    return types.Tool(
        name="mark_as_read",
        description=(
            "Marks one or more Gmail emails as read by removing the UNREAD label. "
            "Accepts a single email ID or a comma-separated list of IDs."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "email_ids": {
                    "type": "string",
                    "description": (
                        "Single email ID or comma-separated list of IDs to mark as read "
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
    results = [(id_, gmail_client.mark_as_read(id_)) for id_ in ids]

    succeeded = [id_ for id_, ok in results if ok]
    failed = [id_ for id_, ok in results if not ok]

    lines = ["📬 Mark as Read — Results", "─" * 40]

    if succeeded:
        lines.append(f"✅ Successfully marked as read ({len(succeeded)}):")
        for id_ in succeeded:
            lines.append(f"   • {id_}")

    if failed:
        lines.append(f"❌ Failed ({len(failed)}):")
        for id_ in failed:
            lines.append(f"   • {id_}")

    return [types.TextContent(type="text", text="\n".join(lines))]
