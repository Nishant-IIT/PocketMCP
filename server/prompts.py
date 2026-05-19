"""
Phase 2 — Prompt definitions.

Prompts are reusable message TEMPLATES. Unlike tools (which execute logic)
or resources (which expose data), prompts return a pre-filled conversation
that the client injects into the LLM context.

Use cases:
  - Give the LLM a consistent starting context for a task.
  - Let users trigger a workflow with one click in a client UI.
  - Build multi-turn conversation starters.

Two return styles shown here:
  1. str            → FastMCP wraps it into a single user Message.
  2. list[Message]  → Multi-turn: you control role, order, and content.

FastMCP's Message class:
  Message("text")                       → user message (default)
  Message("text", role="assistant")     → assistant message
  The mcp.types.PromptMessage is the lower-level MCP type; FastMCP's
  Message is the idiomatic wrapper to use in prompt functions.
"""

from __future__ import annotations

from typing import Literal

from fastmcp import FastMCP
from fastmcp.prompts.base import Message

from server import store


def register_prompts(mcp: FastMCP) -> None:

    # ------------------------------------------------------------------
    # 1. Single-message prompt — returns a str.
    #    FastMCP automatically wraps this in a user Message.
    #    Simple and sufficient for most "give the LLM a task" scenarios.
    # ------------------------------------------------------------------
    @mcp.prompt(description="Ask the LLM to analyse a piece of text.")
    def analyze_text(
        text: str,
        focus: Literal["tone", "clarity", "grammar", "conciseness"] = "clarity",
    ) -> str:
        return (
            f"Please analyse the following text. Focus specifically on {focus}. "
            f"Point out strengths and suggest concrete improvements.\n\n"
            f"---\n{text}\n---"
        )

    # ------------------------------------------------------------------
    # 2. Multi-turn prompt — returns list[Message].
    #    Sets up a short back-and-forth so the LLM has context before
    #    the user's actual question arrives.
    #    role="user" | "assistant" mirrors a real conversation history.
    # ------------------------------------------------------------------
    @mcp.prompt(description="Load a note into context and ask the LLM to review it.")
    def review_note(note_id: str) -> list[Message]:
        note = store.get_note(note_id)

        if note is None:
            return [Message(f"I wanted to review note '{note_id}' but it doesn't exist.")]

        return [
            Message(
                f"I have a note titled '{note['title']}' (ID: {note['id']}):\n\n{note['body']}"
            ),
            Message("I've read your note. What would you like help with?", role="assistant"),
            Message("Please review it and suggest how to make it clearer and more useful."),
        ]
