"""
Server assembly — owns one job: create the FastMCP instance and register everything.

Phase 1: tools registered via mcp.add_tool(fn)
Phase 2: resources + prompts registered via register_*(mcp)
Phase 3: context-aware tools (analyze_texts, note_stats, smart_summarize)
Phase 5: sub-servers mounted via mcp.mount(prefix, sub_server)
        proxy server demonstrates re-exposing a remote server locally

After Phase 5 the inspector will show:
    Tools:     19  (13 flat + 3 text_* + 3 math_*)
    Resources:  2
    Templates:  1
    Prompts:    2

Composition concepts in this file:
    mcp.mount(text_mcp, prefix="text")
        Every tool in text_mcp is imported under the "text" namespace.
        "word_frequency" becomes "text_word_frequency", and so on.
        The sub-server is unaware of the parent — it still works standalone.

    mcp.mount(math_mcp, prefix="math")
        Same pattern for math tools.

    Proxy pattern (shown commented out — needs a running HTTP server):
        proxy = FastMCP.as_proxy("http://localhost:9000/mcp")
        mcp.mount("remote", proxy)
        Every tool/resource/prompt on the remote server is transparently
        re-exposed here, prefixed with "remote_".
"""

from fastmcp import FastMCP

from server.math_server import math_mcp
from server.prompts import register_prompts
from server.resources import register_resources
from server.text_server import text_mcp
from server.tools import (
    analyze_texts,
    change_case,
    create_note,
    current_datetime,
    days_until,
    delete_note,
    is_prime,
    note_stats,
    power,
    smart_summarize,
    sum_numbers,
    truncate,
    word_count,
)

mcp = FastMCP(
    name="PocketMCP",
    instructions=(
        "A personal toolkit server. "
        "Core tools: word_count, change_case, truncate, sum_numbers, is_prime, power, "
        "current_datetime, days_until, create_note, delete_note. "
        "Text analysis (prefixed): text_word_frequency, text_reverse_words, text_extract_numbers. "
        "Advanced math (prefixed): math_factorial, math_gcd, math_stats."
    ),
)

# ---------------------------------------------------------------------------
# Flat tools (Phases 1–3)
# Registered directly — no prefix, no namespace.
# ---------------------------------------------------------------------------
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
mcp.add_tool(analyze_texts)
mcp.add_tool(note_stats)
mcp.add_tool(smart_summarize)

# ---------------------------------------------------------------------------
# Mounted sub-servers (Phase 5)
#
# mount(prefix, sub_server) imports every component from sub_server and
# prepends the prefix + "_" to tool names:
#
#   text_mcp.word_frequency  →  text_word_frequency
#   text_mcp.reverse_words   →  text_reverse_words
#   text_mcp.extract_numbers →  text_extract_numbers
#
#   math_mcp.factorial       →  math_factorial
#   math_mcp.gcd             →  math_gcd
#   math_mcp.stats           →  math_stats
#
# The sub-servers themselves are unchanged — they still run standalone.
# Mounting is non-destructive composition.
# ---------------------------------------------------------------------------
mcp.mount(text_mcp, namespace="text")
mcp.mount(math_mcp, namespace="math")

# ---------------------------------------------------------------------------
# Proxy pattern — uncomment when you have a remote server running.
#
# A proxy re-exposes ALL tools/resources/prompts from a remote MCP server
# as if they were local. The parent server is the single entry point;
# the client never talks to the remote directly.
#
#   proxy = FastMCP.as_proxy("http://localhost:9000/mcp")
#   mcp.mount("remote", proxy)
#
# This is how you build an aggregator server: one URL, many back-ends.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Resources & Prompts
# ---------------------------------------------------------------------------
register_resources(mcp)
register_prompts(mcp)
