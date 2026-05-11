"""
Server assembly — owns one job: create the FastMCP instance and register everything.

Phase 1: tools registered via mcp.add_tool(fn)
Phase 2: resources registered via register_resources(mcp)
         prompts  registered via register_prompts(mcp)
         new note tools added (create_note, delete_note)

After Phase 2 the inspector will show:
  Tools:     10
  Resources:  2  (info://server, notes://all)
  Templates:  1  (notes://{note_id})
  Prompts:    2  (analyze_text, review_note)
"""

from fastmcp import FastMCP

from server.prompts import register_prompts
from server.resources import register_resources
from server.tools import (
    change_case,
    create_note,
    current_datetime,
    days_until,
    delete_note,
    is_prime,
    power,
    sum_numbers,
    truncate,
    word_count,
)

mcp = FastMCP(
    name="PocketMCP",
    instructions=(
        "A personal toolkit server. "
        "Text: word_count, change_case, truncate. "
        "Math: sum_numbers, is_prime, power. "
        "Dates: current_datetime, days_until. "
        "Notes: create_note, delete_note — then read back via notes:// resources."
    ),
)

# --- Tools ---
mcp.add_tool(word_count)
mcp.add_tool(change_case)
mcp.add_tool(truncate)
mcp.add_tool(sum_numbers)
mcp.add_tool(is_prime)
mcp.add_tool(power)
mcp.add_tool(current_datetime)
mcp.add_tool(days_until)
mcp.add_tool(create_note)
mcp.add_tool(delete_note)

# --- Resources & Prompts ---
register_resources(mcp)
register_prompts(mcp)
