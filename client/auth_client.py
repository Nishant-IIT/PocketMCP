"""
Phase 7 — Auth client demo.

Starts the auth server in a background thread on port 8765, then
exercises three scenarios against it over real HTTP:

1. No token       → McpError / connection refused / 401
2. Wrong token    → 401 Unauthorized
3. Correct token  → success + AccessToken contents visible

Run with:
    uv run python -m client.auth_client

Key imports for bearer auth on the client side:
    from fastmcp import Client
    from fastmcp.client.auth.bearer import BearerAuth
    async with Client("http://...", auth=BearerAuth("token")) as client:
    ...

The server URL for streamable-http is:  http://host:port/mcp
"""

from __future__ import annotations

import asyncio
import threading
import time

from fastmcp import Client
from fastmcp.client.auth.bearer import BearerAuth

from server.auth_server import SECRET_TOKEN, auth_mcp

PORT = 8765
BASE_URL = f"http://127.0.0.1:{PORT}/mcp"


# ---------------------------------------------------------------------------
# Start the auth server in a background thread
# ---------------------------------------------------------------------------

def _run_server() -> None:
    auth_mcp.run(transport="streamable-http", port=PORT, log_level="warning")


def start_server() -> None:
    t = threading.Thread(target=_run_server, daemon=True)
    t.start()
    time.sleep(1.5)  # give uvicorn time to bind the port
    print(f"  Server running at {BASE_URL}")


# ---------------------------------------------------------------------------
# Demo helpers
# ---------------------------------------------------------------------------

def banner(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


async def try_call(label: str, token: str | None) -> None:
    """Attempt a tool call with or without a bearer token."""
    auth = BearerAuth(token) if token else None
    print(f"\n  [{label}]")
    print(f"  token : {repr(token)}")
    try:
        async with Client(BASE_URL, auth=auth) as client:
            result = await client.call_tool("whoami", {})
            print(f"  result: {result.data}")
    except Exception as exc:
        # Strip the long traceback — just show the relevant error message
        msg = str(exc).splitlines()[0]
        print(f"  error : {msg}")


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

async def main() -> None:
    print("PocketMCP — Phase 7 Auth Demo")

    banner("SERVER STARTUP")
    start_server()

    banner("1 · TOOL LISTING (no auth needed for discovery)")
    # MCP's list_tools is typically public — auth only gates tool execution.
    async with Client(BASE_URL, auth=BearerAuth(SECRET_TOKEN)) as client:
        tools = await client.list_tools()
        print(f"\n  {len(tools)} tools: {[t.name for t in tools]}")

    banner("2 · CALL WITHOUT TOKEN")
    await try_call("no token", token=None)

    banner("3 · CALL WITH WRONG TOKEN")
    await try_call("wrong token", token="not-the-right-secret")

    banner("4 · CALL WITH CORRECT TOKEN")
    await try_call("correct token", token=SECRET_TOKEN)

    banner("5 · ECHO SECURE — caller identity in response")
    async with Client(BASE_URL, auth=BearerAuth(SECRET_TOKEN)) as client:
        result = await client.call_tool("echo_secure", {"message": "hello from the client"})
        print(f"\n  result: {result.data}")

    banner("6 · ACCESSTOKEN FIELDS")
    async with Client(BASE_URL, auth=BearerAuth(SECRET_TOKEN)) as client:
        result = await client.call_tool("whoami", {})
        print()
        for k, v in result.data.items():
            print(f"  {k:<17} : {v}")

    print("\n\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
