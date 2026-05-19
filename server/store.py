"""
Shared in-memory state for the notes system.

Lives in its own module so both tools.py (write) and resources.py (read)
can import it without creating circular dependencies.

In a real server this would be a database or file system.
"""

from __future__ import annotations

import uuid
from datetime import datetime

_notes: dict[str, dict] = {}


def create_note(title: str, body: str) -> dict:
    note_id = str(uuid.uuid4())[:8]
    note = {
        "id": note_id,
        "title": title,
        "body": body,
        "created_at": datetime.now().isoformat(),
    }
    _notes[note_id] = note
    return note


def get_note(note_id: str) -> dict | None:
    return _notes.get(note_id)


def all_notes() -> dict[str, dict]:
    return dict(_notes)


def delete_note(note_id: str) -> bool:
    if note_id in _notes:
        del _notes[note_id]
        return True
    return False
