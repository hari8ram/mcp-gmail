"""
Gmail MCP Client — client.py
A standalone Python CLI client that communicates with the Gmail MCP server
using the official mcp Python SDK ClientSession (stdio transport).
No AI/LLM required — pure direct tool calling.

Run: python client.py
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ─────────────────────────────────────────────────────────────────────────────
# ANSI colours for terminal output
# ─────────────────────────────────────────────────────────────────────────────

CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"


# ─────────────────────────────────────────────────────────────────────────────
# UI Helpers
# ─────────────────────────────────────────────────────────────────────────────

def print_banner():
    print(f"""
{BOLD}{CYAN}╔════════════════════════════════════════════╗
║         📬  Gmail MCP Client               ║
║   Direct Python client — no LLM needed     ║
╚════════════════════════════════════════════╝{RESET}
""")


def print_tools(tools: list) -> None:
    print(f"\n{BOLD}Available Tools:{RESET}")
    print(f"{'─' * 55}")
    for i, tool in enumerate(tools, start=1):
        desc = tool.description or ""
        short_desc = desc[:75] + "..." if len(desc) > 75 else desc
        print(f"  {CYAN}{i:2}.{RESET} {BOLD}{tool.name}{RESET}")
        print(f"       {DIM}{short_desc}{RESET}")
    print(f"{'─' * 55}")
    print(f"  {CYAN} 0.{RESET} Exit\n")


def prompt_arguments(tool) -> dict:
    """Interactively prompt for tool arguments based on the tool's input schema."""
    schema = tool.input_schema or {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    args = {}

    if not properties:
        return args

    print(f"\n{YELLOW}Enter arguments for '{tool.name}' (press Enter to use defaults):{RESET}")

    for name, prop in properties.items():
        is_required = name in required
        desc = prop.get("description", "")
        default = prop.get("default", None)
        type_hint = prop.get("type", "string")

        req_label = f" {RED}(required){RESET}" if is_required else (
            f" {DIM}[default: {default}]{RESET}" if default is not None else ""
        )
        print(f"  {BOLD}{name}{RESET}{req_label}")
        print(f"  {DIM}{desc}{RESET}")

        raw = input("  > ").strip()

        if raw:
            args[name] = int(raw) if type_hint == "number" else raw
        elif default is not None:
            args[name] = default
        elif is_required:
            print(f"{RED}  ✗ This field is required!{RESET}")
            raw = input("  > ").strip()
            args[name] = int(raw) if type_hint == "number" else raw

    return args


# ─────────────────────────────────────────────────────────────────────────────
# Main interactive loop
# ─────────────────────────────────────────────────────────────────────────────

async def run_interactive(session: ClientSession) -> None:
    # Fetch tool list from server
    tools_result = await session.list_tools()
    tools = tools_result.tools

    print(f"{GREEN}✅ {len(tools)} tools loaded{RESET}")

    while True:
        print_tools(tools)

        try:
            choice = input(f"{BOLD}Select a tool (number): {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{GREEN}👋 Bye!{RESET}\n")
            break

        if choice in ("0", "q", "quit", "exit"):
            print(f"\n{GREEN}👋 Bye!{RESET}\n")
            break

        try:
            index = int(choice) - 1
            if index < 0 or index >= len(tools):
                print(f"{RED}Invalid choice. Try again.{RESET}\n")
                continue
        except ValueError:
            print(f"{RED}Please enter a number.{RESET}\n")
            continue

        tool = tools[index]
        args = prompt_arguments(tool)

        print(f"\n{DIM}Calling '{tool.name}'...{RESET}\n")
        print("─" * 60)

        try:
            result = await session.call_tool(tool.name, args)
            # Print each content block
            for block in result.content:
                if hasattr(block, "text"):
                    print(block.text)
        except Exception as e:
            print(f"{RED}❌ Error: {e}{RESET}")

        print("─" * 60)

        try:
            input(f"\n{DIM}Press Enter to continue...{RESET}")
        except (EOFError, KeyboardInterrupt):
            print(f"\n{GREEN}👋 Bye!{RESET}\n")
            break
        print()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    base_dir = Path(__file__).parent.resolve()
    python_path = str(base_dir / "venv" / "bin" / "python")

    if not Path(python_path).exists():
        print(f"{RED}❌ venv not found. Run:{RESET}")
        print("   python3 -m venv venv && pip install -r requirements.txt")
        sys.exit(1)

    print_banner()
    print(f"{DIM}Starting Gmail MCP server...{RESET}\n")

    server_params = StdioServerParameters(
        command=python_path,
        args=["-m", "src.server"],
        cwd=str(base_dir),
        env={
            "CREDENTIALS_PATH": str(base_dir / "credentials/credentials.json"),
            "TOKEN_PATH": str(base_dir / "credentials/token.json"),
        },
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # MCP handshake — SDK handles this automatically
                await session.initialize()
                print(f"{GREEN}✅ Connected to Gmail MCP Server{RESET}")

                await run_interactive(session)

    except FileNotFoundError as e:
        print(f"\n{RED}❌ {e}{RESET}")
        print(f"{YELLOW}Run: python -m src.auth  to set up Gmail credentials first.{RESET}")
        sys.exit(1)
    except Exception as e:
        msg = str(e)
        if "credentials" in msg.lower() or "token" in msg.lower():
            print(f"\n{RED}❌ Gmail credentials not set up yet.{RESET}")
            print(f"{YELLOW}Steps:\n  1. Add credentials.json to credentials/\n  2. Run: python -m src.auth{RESET}")
        else:
            print(f"\n{RED}❌ Error: {e}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{GREEN}👋 Interrupted. Bye!{RESET}")
