"""
Phase 2 — Resource definitions.

Resources are READ-ONLY data sources identified by a URI.
The LLM (or client) can request them, but cannot call them like tools.

Three kinds shown here:
  1. Static resource  — fixed URI, same content every call   (info://server)
  2. List resource    — fixed URI, dynamic content           (notes://all)
  3. Template resource — URI with a {param} placeholder     (notes://{note_id})

Key differences from tools:
  - Resources have a URI, tools have a name.
  - Resources are for READ access; tools are for actions / writes.
  - Resources support MIME types so clients know how to render the content.
  - Template resources are listed separately from regular resources in the
    MCP spec — clients must know to expand the template before fetching.

We use a register_resources(mcp) helper so resource logic lives here
but registration happens on the single mcp instance in server.py.
"""

from __future__ import annotations

import json

from fastmcp import FastMCP

from server import store


def register_resources(mcp: FastMCP) -> None:

    # ------------------------------------------------------------------
    # 1. Static resource — plain text, fixed URI, content never changes
    # ------------------------------------------------------------------
    @mcp.resource("info://server", mime_type="text/plain", description="Overview of PocketMCP's tools and resources.")
    def server_info() -> str:
        return (
            "PocketMCP — Personal Toolkit Server\n"
            "\n"
            "Tools\n"
            "  Text   : word_count, change_case, truncate\n"
            "  Math   : sum_numbers, is_prime, power\n"
            "  Dates  : current_datetime, days_until\n"
            "  Notes  : create_note, delete_note\n"
            "\n"
            "Resources\n"
            "  info://server         — this help text\n"
            "  notes://all           — all notes as JSON\n"
            "  notes://{note_id}     — a single note by ID\n"
        )

    # ------------------------------------------------------------------
    # 2. List resource — fixed URI, but content is dynamic (reads store)
    # ------------------------------------------------------------------
    @mcp.resource(
        "notes://all",
        mime_type="application/json",
        description="All stored notes, keyed by note ID.",
    )
    def list_all_notes() -> str:
        return json.dumps(store.all_notes(), indent=2)

    # ------------------------------------------------------------------
    # 3. Template resource — URI contains a {note_id} placeholder.
    #    FastMCP registers this as a ResourceTemplate, not a Resource.
    #    Clients expand the template: notes://abc123 → fetches that note.
    # ------------------------------------------------------------------
    @mcp.resource(
        "notes://{note_id}",
        mime_type="application/json",
        description="A single note. Replace {note_id} with the actual ID.",
    )
    def get_single_note(note_id: str) -> str:
        note = store.get_note(note_id)
        if note is None:
            return json.dumps({"error": f"Note '{note_id}' not found."})
        return json.dumps(note, indent=2)
