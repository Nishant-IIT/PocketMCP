"""
Phase 6 — Custom middleware.

Middleware intercepts every MCP request before it reaches the handler and
every response before it goes back to the client. It is the right place for
cross-cutting concerns that should not live inside tool logic.

FastMCP middleware model:
    - Subclass Middleware and override one or more on_* methods.
    - Each method receives (context, call_next).
    - Calling await call_next(context) passes the request deeper into the stack.
    - Code before call_next runs on the way IN.
    - Code after call_next runs on the way OUT.
    - Raising an exception short-circuits all downstream handlers.

Available hooks (all optional — only override what you need):
    on_message         — every message, any type
    on_request         — every request (tools, resources, prompts, listing)
    on_call_tool       — tool execution only
    on_read_resource   — resource reads only
    on_get_prompt      — prompt rendering only
    on_list_tools      — tool listing only
    on_list_resources  — resource listing only
    on_list_prompts    — prompt listing only

Execution order when three middlewares A → B → C are added:
    request  →  A.before  →  B.before  →  C.before  →  [tool]
    response ←  A.after   ←  B.after   ←  C.after   ←  [tool]
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from fastmcp.server.middleware.middleware import (
    CallNext,
    Middleware,
    MiddlewareContext,
)
from fastmcp.tools.base import ToolResult


# ---------------------------------------------------------------------------
# 1. CallStatsMiddleware
#
# Tracks per-tool call counts, cumulative execution time, and error counts.
# Demonstrates: stateful middleware, before/after pattern, error detection.
# Access stats any time via middleware_instance.report().
# ---------------------------------------------------------------------------

@dataclass
class _ToolStats:
    calls:      int   = 0
    errors:     int   = 0
    total_ms:   float = 0.0

    @property
    def avg_ms(self) -> float:
        return self.total_ms / self.calls if self.calls else 0.0


class CallStatsMiddleware(Middleware):
    """
    Record call count, error count, and average latency for every tool.
    The stats dict is keyed by tool name and updated on every call.
    """

    def __init__(self) -> None:
        self._stats: dict[str, _ToolStats] = defaultdict(_ToolStats)

    async def on_call_tool(
        self,
        context: MiddlewareContext,
        call_next: CallNext,
    ) -> ToolResult:
        name = context.message.name
        stat = self._stats[name]
        stat.calls += 1

        start = time.monotonic()
        try:
            result = await call_next(context)
            stat.total_ms += (time.monotonic() - start) * 1000
            return result
        except Exception:
            stat.total_ms += (time.monotonic() - start) * 1000
            stat.errors += 1
            raise  # re-raise so outer middleware (ErrorHandlingMiddleware) handles it

    def report(self) -> dict[str, dict]:
        return {
            name: {
                "calls":    s.calls,
                "errors":   s.errors,
                "avg_ms":   round(s.avg_ms, 2),
                "total_ms": round(s.total_ms, 2),
            }
            for name, s in sorted(self._stats.items())
        }


# ---------------------------------------------------------------------------
# 2. BlocklistMiddleware
#
# Rejects calls to a configurable set of tool names before they reach the
# handler. Demonstrates: short-circuiting (not calling call_next), raising
# exceptions from middleware, and per-request decision logic.
# ---------------------------------------------------------------------------

class BlocklistMiddleware(Middleware):
    """
    Prevent specific tools from being called.
    Useful for disabling tools at runtime without removing them from the server.
    Raise PermissionError so the client sees a meaningful error message.
    """

    def __init__(self, blocked: set[str]) -> None:
        self._blocked = blocked

    async def on_call_tool(
        self,
        context: MiddlewareContext,
        call_next: CallNext,
    ) -> ToolResult:
        name = context.message.name
        if name in self._blocked:
            raise PermissionError(
                f"Tool '{name}' is currently disabled by the server administrator."
            )
        return await call_next(context)


# ---------------------------------------------------------------------------
# 3. ArgumentLoggerMiddleware
#
# Logs the name and arguments of every tool call. Demonstrates: reading
# request data from context.message before forwarding, structured logging,
# and using on_call_tool without modifying the response.
# ---------------------------------------------------------------------------

class ArgumentLoggerMiddleware(Middleware):
    """
    Print each tool call's name and arguments to stdout as it arrives.
    In production you'd write to a structured logger or audit trail instead.
    """

    def __init__(self, max_arg_len: int = 80) -> None:
        self._max = max_arg_len

    async def on_call_tool(
        self,
        context: MiddlewareContext,
        call_next: CallNext,
    ) -> ToolResult:
        name = context.message.name
        args = dict(context.message.arguments or {})

        truncated = {
            k: (str(v)[:self._max] + "…" if len(str(v)) > self._max else v)
            for k, v in args.items()
        }
        print(f"  [audit] {name}({truncated})")

        try:
            result = await call_next(context)
            print(f"  [audit] {name} → OK")
            return result
        except Exception as exc:
            print(f"  [audit] {name} → ERROR: {exc}")
            raise
