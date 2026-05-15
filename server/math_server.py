"""
Phase 5 — Math sub-server.

A fully self-contained FastMCP server that owns advanced math tools.
Demonstrates that sub-servers are just regular FastMCP instances —
they carry their own tools, resources, and prompts if needed.

Run standalone:   fastmcp dev server/math_server.py
Mount into main:  mcp.mount("math", math_mcp)
    → tools become  math_factorial, math_gcd, math_stats
"""

from __future__ import annotations

import math
import statistics

from fastmcp import FastMCP

math_mcp = FastMCP(
    name="MathTools",
    instructions="Advanced math utilities: combinatorics, number theory, statistics.",
)


@math_mcp.tool
def factorial(n: int) -> int:
    """
    Calculate n! (n factorial).
    Raises ValueError for negative inputs.
    Example: factorial(5) → 120
    """
    if n < 0:
        raise ValueError(f"factorial is not defined for negative numbers (got {n})")
    return math.factorial(n)


@math_mcp.tool
def gcd(a: int, b: int) -> int:
    """
    Find the greatest common divisor of two integers.
    Example: gcd(12, 8) → 4
    """
    return math.gcd(a, b)


@math_mcp.tool
def stats(numbers: list[float]) -> dict:
    """
    Calculate descriptive statistics for a list of numbers.
    Returns mean, median, standard deviation, min, and max.
    Requires at least two numbers for standard deviation.
    """
    if not numbers:
        raise ValueError("Cannot compute statistics on an empty list.")
    result: dict = {
        "mean":   statistics.mean(numbers),
        "median": statistics.median(numbers),
        "min":    min(numbers),
        "max":    max(numbers),
    }
    if len(numbers) >= 2:
        result["stdev"] = statistics.stdev(numbers)
    return result
