"""
Server assembly — owns one job: create the FastMCP instance and register everything.

Phase 1: tools registered via mcp.add_tool(fn)
Phase 2: resources + prompts registered via register_*(mcp)
Phase 3: context-aware tools (analyze_texts, note_stats, smart_summarize)
Phase 5: sub-servers mounted via mcp.mount(sub_server, namespace=...)
Phase 6: middleware stack added via mcp.add_middleware(...)

After Phase 6 the inspector still shows:
    Tools:     19
    Resources:  2
    Templates:  1
    Prompts:    2
Middleware is invisible to the inspector — it wraps the stack at runtime.

Middleware execution order (outermost → innermost):
    LoggingMiddleware        — logs every request/response at DEBUG level
    TimingMiddleware         — logs execution time per call
    RateLimitingMiddleware   — enforces a per-second request cap
    ArgumentLoggerMiddleware — prints tool name + args to stdout (custom)
    CallStatsMiddleware      — accumulates per-tool call stats (custom)

The onion model:
    request  →  Logging → Timing → RateLimit → ArgLogger → Stats → [tool]
    response ←  Logging ← Timing ← RateLimit ← ArgLogger ← Stats ← [tool]
"""

from fastmcp import FastMCP
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware

from server.math_server import math_mcp
from server.middleware import ArgumentLoggerMiddleware, CallStatsMiddleware
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
# Middleware stack (Phase 6)
# Order matters: first added = outermost wrapper.
# ---------------------------------------------------------------------------

# Built-in: structured DEBUG-level logging for every request/response
mcp.add_middleware(LoggingMiddleware())

# Built-in: logs wall-clock time for every tool call / resource read
mcp.add_middleware(TimingMiddleware())

# Built-in: token-bucket rate limiter — 20 requests/second globally
mcp.add_middleware(RateLimitingMiddleware(max_requests_per_second=20.0))

# Built-in: catches exceptions from tools and returns them as MCP errors
# instead of crashing the server
mcp.add_middleware(ErrorHandlingMiddleware())

# Custom: prints tool name + args to stdout on every call
mcp.add_middleware(ArgumentLoggerMiddleware(max_arg_len=60))

# Custom: keeps per-tool call/error/latency stats; exported as `call_stats`
# so the client demo can query it directly via the Python object reference.
call_stats = CallStatsMiddleware()
mcp.add_middleware(call_stats)

# ---------------------------------------------------------------------------
# Flat tools (Phases 1–3)
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
# ---------------------------------------------------------------------------
mcp.mount(text_mcp, namespace="text")
mcp.mount(math_mcp, namespace="math")

# ---------------------------------------------------------------------------
# Resources & Prompts
# ---------------------------------------------------------------------------
register_resources(mcp)
register_prompts(mcp)
