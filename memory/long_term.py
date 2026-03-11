"""
long_term.py — JSON file-based persistent memory across sessions.

Saves student preferences, past topics, bookmarked resources,
and session summaries to disk so they survive restarts.
"""

import json
import os
import datetime
from typing import Any, Optional

DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memory",
    "long_term_store.json",
)


class LongTermMemory:
    """
    Persistent key-value memory backed by a JSON file.

    Automatically loads existing data on init and saves on every write.

    Usage:
        ltm = LongTermMemory()
        ltm.set("preferred_subject", "Math")
        ltm.add_session_summary("Asked about quadratic equations")
    """

    def __init__(self, filepath: str = DEFAULT_PATH):
        """
        Initialize and load existing data from disk.

        Args:
            filepath: Path to the JSON storage file.
        """
        self._filepath = filepath
        self._data: dict = self._load()

    # ── Core store ────────────────────────────────────────────────────────────

    def _load(self) -> dict:
        """Load data from disk, returning empty dict on failure."""
        try:
            if os.path.exists(self._filepath):
                with open(self._filepath, "r") as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[long_term] Load error: {e}")
        return {"facts": {}, "sessions": [], "bookmarks": []}

    def _save(self) -> None:
        """Write current data to disk."""
        try:
            os.makedirs(os.path.dirname(self._filepath), exist_ok=True)
            with open(self._filepath, "w") as f:
                json.dump(self._data, f, indent=2)
        except OSError as e:
            print(f"[long_term] Save error: {e}")

    def set(self, key: str, value: Any) -> None:
        """
        Store a fact under key (persisted immediately).

        Args:
            key:   Fact identifier (e.g., "student_name").
            value: The value to store.
        """
        self._data.setdefault("facts", {})[key] = value
        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a stored fact.

        Args:
            key:     Fact identifier.
            default: Value if key not found.

        Returns:
            Stored value or default.
        """
        return self._data.get("facts", {}).get(key, default)

    def delete(self, key: str) -> None:
        """Remove a stored fact."""
        self._data.get("facts", {}).pop(key, None)
        self._save()

    def all_facts(self) -> dict:
        """Return all stored facts."""
        return dict(self._data.get("facts", {}))

    # ── Session log ───────────────────────────────────────────────────────────

    def add_session_summary(self, summary: str) -> None:
        """
        Log a summary of the current session for future reference.

        Args:
            summary: Plain-text description of what was accomplished.
        """
        self._data.setdefault("sessions", []).append({
            "date": datetime.date.today().isoformat(),
            "summary": summary,
        })
        # Keep last 50 sessions
        self._data["sessions"] = self._data["sessions"][-50:]
        self._save()

    def get_recent_sessions(self, n: int = 5) -> list[dict]:
        """
        Return the most recent N session summaries.

        Args:
            n: Number of sessions to return.

        Returns:
            List of {"date": str, "summary": str} dicts.
        """
        return self._data.get("sessions", [])[-n:]

    # ── Bookmarks ─────────────────────────────────────────────────────────────

    def add_bookmark(self, title: str, url: str, subject: str = "") -> None:
        """
        Save a useful resource URL.

        Args:
            title:   Human-readable title.
            url:     Resource URL.
            subject: Subject area (e.g., "Math", "Science").
        """
        self._data.setdefault("bookmarks", []).append({
            "title": title,
            "url": url,
            "subject": subject,
            "saved": datetime.date.today().isoformat(),
        })
        self._save()

    def get_bookmarks(self, subject: str = "") -> list[dict]:
        """
        Return saved bookmarks, optionally filtered by subject.

        Args:
            subject: If provided, only return bookmarks for this subject.

        Returns:
            List of bookmark dicts.
        """
        bookmarks = self._data.get("bookmarks", [])
        if subject:
            return [b for b in bookmarks if b.get("subject", "").lower() == subject.lower()]
        return bookmarks

    def context_summary(self) -> str:
        """Return a formatted string of key facts for injecting into prompts."""
        facts = self.all_facts()
        if not facts:
            return "No long-term context stored yet."
        lines = ["Remembered facts about this student:"]
        for k, v in facts.items():
            lines.append(f"  • {k}: {v}")
        return "\n".join(lines)

    # ── Conversation history ───────────────────────────────────────────────────

    def add_conversation_turn(self, role: str, content: str, agent: str = "") -> None:
        """
        Save a conversation turn (capped at 40 turns total).

        Args:
            role:    "user" or "assistant".
            content: Message text (truncated to 1000 chars for storage).
            agent:   Which agent produced this (for assistant turns).
        """
        conv = self._data.setdefault("conversation", [])
        conv.append({
            "role": role,
            "content": str(content)[:1000],
            "agent": agent,
            "ts": datetime.datetime.now().isoformat(),
        })
        self._data["conversation"] = conv[-40:]
        self._save()

    def get_conversation_history(self, last_n: int = 10) -> list:
        """Return the last N conversation turns."""
        return self._data.get("conversation", [])[-last_n:]

    def format_history_for_prompt(self, last_n: int = 6) -> str:
        """Return recent history as a formatted string for prompt injection."""
        turns = self.get_conversation_history(last_n)
        if not turns:
            return ""
        lines = ["Recent conversation history (for context):"]
        for t in turns:
            label = "Student" if t["role"] == "user" else f"Assistant"
            lines.append(f"  {label}: {str(t['content'])[:400]}")
        return "\n".join(lines)
