"""
Phase 4 — FastMCP Client

Drives the PocketMCP server programmatically: lists components,
calls tools, reads resources, and renders prompts.

Three transports are shown at the bottom of this file.
This script uses in-memory transport so you can run it with:

    uv run python client/client.py

No separate server process needed.

Key things to notice:
  - The client API mirrors the three MCP primitives exactly.
  - Tool results come back as a list of content objects (same shape
    Claude receives), not unwrapped values — you parse them yourself.
  - Server-side ctx.info() / ctx.warning() calls arrive here as log
    notifications if you register a log handler on the client.
  - Swapping from in-memory → stdio → HTTP changes zero application code.
"""

from __future__ import annotations

import asyncio
import json

from fastmcp import Client

# In-memory transport: hand the FastMCP instance to the Client directly.
# The Client communicates with it inside the same process — no subprocess,
# no network, instant startup. Ideal for scripts and tests.
from server.server import mcp as pocket_mcp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def parse(result) -> object:
    """
    call_tool returns a CallToolResult.
    .data        — the unwrapped Python value (FastMCP 3.x convenience field)
    .content     — list[TextContent], the raw MCP content (what Claude sees)
    .is_error    — True if the tool raised an exception
    """
    return result.data


# ---------------------------------------------------------------------------
# Log handler — receives ctx.info / ctx.warning / ctx.error calls live
# ---------------------------------------------------------------------------

async def on_log(message) -> None:
    level = message.level.upper()
    # message.data is {"msg": "...", "extra": None} from FastMCP's logger
    text = message.data.get("msg", message.data) if isinstance(message.data, dict) else message.data
    print(f"    [server {level}] {text}")


# ---------------------------------------------------------------------------
# Section 1 — Tools
# ---------------------------------------------------------------------------

async def demo_tools(client: Client) -> None:
    banner("1 · LIST TOOLS")

    tools = await client.list_tools()
    print(f"  {len(tools)} tools registered:\n")

    for t in tools:
        schema = t.inputSchema
        required = schema.get("required", [])
        optional = [k for k in schema.get("properties", {}) if k not in required]
        parts = []
        if required:
            parts.append(f"required={required}")
        if optional:
            parts.append(f"optional={optional}")
        print(f"  {t.name:25s}  {', '.join(parts)}")

    banner("2 · CALL TOOLS — raw result shape")

    # Show the raw result before we start parsing, so you see what
    # the client actually receives (same structure Claude gets).
    raw = await client.call_tool("is_prime", {"n": 17})
    print(f"\n  raw type              : {type(raw).__name__}")
    print(f"  raw.is_error          : {raw.is_error}")
    print(f"  raw.content[0].type   : {raw.content[0].type}")
    print(f"  raw.content[0].text   : {raw.content[0].text}  ← what Claude sees")
    print(f"  raw.structured_content: {raw.structured_content}")
    print(f"  raw.data              : {raw.data}  ← unwrapped Python value")
    print(f"  parse(raw)            : {parse(raw)}")

    banner("3 · CALL TOOLS — results")

    calls = [
        ("word_count",       {"text": "The quick brown fox jumps over the lazy dog."}),
        ("change_case",      {"text": "hello world", "case": "snake"}),
        ("truncate",         {"text": "This sentence will be cut short.", "max_length": 20}),
        ("sum_numbers",      {"numbers": [1.5, 2.5, 3.0, 4.0]}),
        ("is_prime",         {"n": 97}),
        ("power",            {"base": 8, "exponent": 1/3}),
        ("current_datetime", {}),
        ("days_until",       {"target_date": "2027-01-01"}),
    ]

    for name, args in calls:
        result = await client.call_tool(name, args)
        print(f"  {name:25s} → {parse(result)}")

    banner("4 · CONTEXT TOOL — logs stream back during execution")

    # analyze_texts uses ctx.info(), ctx.warning(), ctx.report_progress().
    # Those arrive here via on_log() as the tool runs.
    print()
    result = await client.call_tool(
        "analyze_texts",
        {"texts": ["Hello world.", "MCP is powerful!", "", "One two three four five."]},
    )
    print(f"\n  final result → {parse(result)}")


# ---------------------------------------------------------------------------
# Section 2 — Resources
# ---------------------------------------------------------------------------

async def demo_resources(client: Client) -> None:
    banner("5 · LIST RESOURCES & TEMPLATES")

    resources  = await client.list_resources()
    templates  = await client.list_resource_templates()

    print(f"  Resources ({len(resources)}):")
    for r in resources:
        print(f"    {str(r.uri):<30s} [{r.mimeType}]")

    print(f"\n  Templates ({len(templates)}):")
    for t in templates:
        print(f"    {str(t.uriTemplate):<30s} [{t.mimeType}]")

    banner("6 · READ RESOURCES")

    # Static resource — same every call
    contents = await client.read_resource("info://server")
    print("  info://server →")
    for line in contents[0].text.splitlines():
        print(f"    {line}")

    # Create two notes so the list resource has data
    r1 = await client.call_tool("create_note", {"title": "First note", "body": "Resources expose data via URIs."})
    r2 = await client.call_tool("create_note", {"title": "Second note", "body": "Tools are actions. Resources are data."})
    id1 = parse(r1)["id"]
    id2 = parse(r2)["id"]
    print(f"\n  Created notes: {id1}, {id2}")

    # Dynamic list resource
    contents = await client.read_resource("notes://all")
    notes = json.loads(contents[0].text)
    print(f"\n  notes://all → {len(notes)} note(s):")
    for nid, note in notes.items():
        print(f"    [{nid}] {note['title']}")

    # Template resource — expand notes://{note_id} with a real ID
    contents = await client.read_resource(f"notes://{id1}")
    note = json.loads(contents[0].text)
    print(f"\n  notes://{id1} →")
    print(f"    title : {note['title']}")
    print(f"    body  : {note['body']}")

    # note_stats uses ctx.read_resource() internally
    print()
    result = await client.call_tool("note_stats", {"note_id": id1})
    print(f"  note_stats({id1}) → {parse(result)}")


# ---------------------------------------------------------------------------
# Section 3 — Prompts
# ---------------------------------------------------------------------------

async def demo_prompts(client: Client) -> None:
    banner("7 · LIST PROMPTS")

    prompts = await client.list_prompts()
    print(f"  {len(prompts)} prompts:\n")
    for p in prompts:
        args = [(a.name, "required" if a.required else "optional") for a in (p.arguments or [])]
        print(f"  {p.name}")
        for name, req in args:
            print(f"    {name} ({req})")

    banner("8 · GET PROMPTS — rendered message lists")

    # Single-message prompt (str return → wrapped in one UserMessage)
    rendered = await client.get_prompt(
        "analyze_text",
        {"text": "FastMCP makes MCP servers easy to build.", "focus": "tone"},
    )
    print(f"\n  analyze_text → {len(rendered.messages)} message(s):")
    for msg in rendered.messages:
        print(f"    role    : {msg.role}")
        print(f"    content : {msg.content.text[:100]}...")

    # Multi-turn prompt (list[PromptMessage] return)
    contents = await client.read_resource("notes://all")
    notes = json.loads(contents[0].text)
    first_id = next(iter(notes))

    rendered = await client.get_prompt("review_note", {"note_id": first_id})
    print(f"\n  review_note → {len(rendered.messages)} message(s):")
    for msg in rendered.messages:
        print(f"    [{msg.role:9s}] {msg.content.text[:70]}...")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    print("PocketMCP — Phase 4 Client Demo")
    print("Transport : in-memory (same process)")

    # -----------------------------------------------------------------------
    # Transport options — all three are API-identical; only the constructor
    # argument changes:
    #
    #   In-memory  →  Client(pocket_mcp)
    #   stdio      →  Client("main.py")
    #                 (FastMCP launches `python main.py` as a subprocess)
    #   HTTP       →  Client("http://localhost:8000/mcp")
    #                 (run `uv run fastmcp run main.py --transport http` first)
    # -----------------------------------------------------------------------

    async with Client(pocket_mcp, log_handler=on_log) as client:
        # Basic server interaction
        await client.ping()
        
        # List available operations
        await demo_tools(client)
        await demo_resources(client)
        await demo_prompts(client)

    print("\n\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
