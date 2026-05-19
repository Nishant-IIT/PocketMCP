"""
Phases 1, 2 & 3 — Tool definitions.

Key things to observe in this file:
  - Tools are plain Python functions. No MCP-specific code here at all.
  - Type hints become the JSON schema the LLM sees.
  - The docstring becomes the tool description shown to the LLM.
  - Default parameter values make parameters optional in the schema.
  - Return type is serialised and sent back as the tool result.

Types used here and what they produce in JSON schema:
  str           → { "type": "string" }
  int           → { "type": "integer" }
  float         → { "type": "number" }
  bool          → { "type": "boolean" }
  list[float]   → { "type": "array", "items": { "type": "number" } }
  dict          → { "type": "object" }
  Literal[...]  → { "type": "string", "enum": [...] }

Phase 2 note:
  Tools WRITE state (create_note, delete_note).
  Resources READ state (notes://all, notes://{note_id}).
  This separation is a core MCP design principle.

Phase 3 note:
  ctx: Context is injected by FastMCP at call time.
  It does NOT appear in the tool's JSON schema — the LLM never sees it.
  Any tool can gain ctx by adding it to its signature.
  Phase 3 tools are async because ctx methods (logging, progress,
  read_resource, sample) are all coroutines.
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime
from typing import Literal

from fastmcp import Context

from server import store


# ---------------------------------------------------------------------------
# Text tools
# ---------------------------------------------------------------------------

def word_count(text: str) -> dict:
    """
    Count words, characters, and sentences in a piece of text.
    Returns a breakdown with four counts.
    """
    words = len(text.split())
    chars = len(text)
    chars_no_spaces = len(text.replace(" ", ""))
    sentences = text.count(".") + text.count("!") + text.count("?")
    return {
        "words": words,
        "characters": chars,
        "characters_no_spaces": chars_no_spaces,
        "sentences": sentences,
    }


def change_case(text: str, case: Literal["upper", "lower", "title", "snake"]) -> str:
    """
    Convert text to a specific casing style.

    Options:
    - upper: HELLO WORLD
    - lower: hello world
    - title: Hello World
    - snake: hello_world
    """
    if case == "upper":
        return text.upper()
    if case == "lower":
        return text.lower()
    if case == "title":
        return text.title()
    return "_".join(text.lower().split())


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length, appending a suffix if cut short.
    Useful for creating previews of long content.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


# ---------------------------------------------------------------------------
# Math tools
# ---------------------------------------------------------------------------

def sum_numbers(numbers: list[float]) -> float:
    """
    Sum a list of numbers. Accepts both integers and floats.
    Example: [1, 2.5, 3] → 6.5
    """
    return sum(numbers)


def is_prime(n: int) -> bool:
    """
    Check whether a positive integer is a prime number.
    Returns True if prime, False otherwise.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def power(base: float, exponent: float) -> float:
    """
    Raise base to the power of exponent.
    Supports fractional exponents for roots, e.g. power(8, 1/3) → 2.0.
    """
    return base ** exponent


# ---------------------------------------------------------------------------
# Notes tools  (Phase 2)
# These are the WRITE side of the notes system.
# The READ side lives in resources.py as resources (notes://all, notes://{id}).
# ---------------------------------------------------------------------------

def create_note(title: str, body: str) -> dict:
    """
    Create a new note and store it in memory.
    Returns the full note object including its auto-generated ID.
    Use the returned ID to fetch the note later via the notes://{note_id} resource.
    """
    return store.create_note(title, body)


def delete_note(note_id: str) -> bool:
    """
    Delete a note by its ID.
    Returns True if the note was found and deleted, False if it did not exist.
    """
    return store.delete_note(note_id)


# ---------------------------------------------------------------------------
# Datetime tools
# ---------------------------------------------------------------------------

def current_datetime() -> str:
    """
    Return the current local date and time in ISO 8601 format.
    Example output: 2026-05-11T14:32:01.123456
    """
    return datetime.now().isoformat()


def days_until(target_date: str) -> int:
    """
    Calculate the number of days from today until a target date.
    Accepts dates in YYYY-MM-DD format.
    Returns a negative number for dates in the past.
    """
    target = date.fromisoformat(target_date)
    return (target - date.today()).days


# ---------------------------------------------------------------------------
# Phase 3 — Context tools
#
# ctx: Context is identified by its type annotation and injected by FastMCP.
# It is stripped from the JSON schema so the LLM never knows it exists.
# All three tools are async because ctx methods are coroutines.
# ---------------------------------------------------------------------------

async def analyze_texts(texts: list[str], ctx: Context) -> list[dict]:
    """
    Run word_count on a list of texts, reporting progress after each one.
    Logs a warning for any empty string and skips it.
    Demonstrates: ctx.info(), ctx.warning(), ctx.report_progress().
    """
    results = []
    total = len(texts)

    await ctx.info(f"Starting batch analysis of {total} text(s).")

    for i, text in enumerate(texts):
        await ctx.report_progress(i, total)

        if not text.strip():
            await ctx.warning(f"Text at index {i} is empty — skipping.")
            continue

        await ctx.info(f"Analysing text {i + 1}/{total}...")
        counts = word_count(text)
        counts["index"] = i
        results.append(counts)

    await ctx.report_progress(total, total)
    await ctx.info("Batch analysis complete.")
    return results


async def note_stats(note_id: str, ctx: Context) -> dict:
    """
    Fetch a note via its MCP resource URI and return word-count statistics.
    Demonstrates: ctx.read_resource() — a tool reading from a resource.
    This is how tools and resources compose: tools can pull resource data
    without duplicating the fetch logic.
    """
    await ctx.info(f"Reading resource notes://{note_id} ...")

    # ctx.read_resource() returns a ResourceResult (server-side type).
    # Its .contents list holds the actual TextResourceContents items.
    # This is different from client.read_resource() which returns the list directly.
    resource_result = await ctx.read_resource(f"notes://{note_id}")
    if not resource_result.contents:
        await ctx.error(f"Resource notes://{note_id} returned no content.")
        return {"error": f"Note '{note_id}' not found."}

    # Server-side ResourceContent uses .content (str), not .text.
    # Client-side TextResourceContents uses .text — different types, same data.
    raw = resource_result.contents[0].content
    note = json.loads(raw)

    if "error" in note:
        await ctx.error(note["error"])
        return note

    await ctx.info("Resource fetched. Running word count...")
    stats = word_count(note["body"])
    stats["note_id"] = note_id
    stats["title"] = note["title"]
    return stats


async def smart_summarize(text: str, ctx: Context) -> str:
    """
    Ask the LLM to summarise text using MCP sampling (ctx.sample).
    Sampling lets the SERVER trigger an LLM call; the client (Claude, etc.)
    fulfils the request and sends the response back.

    Important: sampling only works with clients that declare the sampling
    capability (e.g. Claude Desktop, programmatic FastMCP clients).
    The MCP inspector does not support it — calling this tool there will
    raise a McpError. That is expected behaviour, not a bug.
    """
    await ctx.info("Requesting LLM summary via sampling...")

    prompt = (
        "Summarise the following text in two or three concise sentences. "
        "Do not add commentary — just the summary.\n\n"
        f"{text}"
    )

    result = await ctx.sample(prompt)
    await ctx.info("Sampling complete.")
    return result.text
