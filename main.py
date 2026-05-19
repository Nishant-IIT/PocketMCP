"""
Entry point for PocketMCP.

`fastmcp dev main.py`  — runs with the MCP inspector (browser UI to test tools)
`fastmcp run main.py`  — runs as a plain stdio server
`python main.py`       — same as fastmcp run (stdio)

FastMCP discovers the `mcp` object imported at module level.
"""

from server.server import mcp

if __name__ == "__main__":
    mcp.run()
