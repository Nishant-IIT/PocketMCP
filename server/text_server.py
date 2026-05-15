"""
Phase 5 — Text sub-server.

A fully self-contained FastMCP server that owns text-analysis tools.
It knows nothing about the parent server — it can run standalone OR
be mounted into a larger server.

Run standalone:   fastmcp dev server/text_server.py
Mount into main:  mcp.mount("text", text_mcp)
    → tools become  text_word_frequency, text_reverse_words, ...
"""

from __future__ import annotations

import re
from collections import Counter

from fastmcp import FastMCP

text_mcp = FastMCP(
    name="TextTools",
    instructions="Utilities for analysing and transforming text.",
)


@text_mcp.tool
def word_frequency(text: str) -> dict:
    """
    Count how many times each word appears in the text.
    Returns a dict sorted by frequency descending.
    Punctuation and casing are normalised before counting.
    """
    words = re.findall(r"[a-zA-Z']+", text.lower())
    counts = Counter(words)
    return dict(counts.most_common())


@text_mcp.tool
def reverse_words(text: str) -> str:
    """
    Reverse the order of words in a sentence while keeping each word intact.
    Example: "hello world" → "world hello"
    """
    return " ".join(text.split()[::-1])


@text_mcp.tool
def extract_numbers(text: str) -> list[float]:
    """
    Find and return every number embedded in a piece of text.
    Handles integers and decimals. Example: "I owe $3.50 and 12 apples" → [3.5, 12.0]
    """
    return [float(n) for n in re.findall(r"-?\d+\.?\d*", text)]
