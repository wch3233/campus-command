"""
short_term.py — In-memory short-term storage for the current session.

Stores the conversation history and intermediate agent results
for the duration of one main.py run. Cleared when the program exits.
"""

from typing import Any


class ShortTermMemory:
    """
    Thread-local in-memory key-value store for the current session.

    Usage:
        mem = ShortTermMemory()
        mem.set("last_query", "What is mitosis?")
        mem.get("last_query")  # → "What is mitosis?"
    """

    def __init__(self):
        """Initialize an empty memory store."""
        self._store: dict[str, Any] = {}
        self._history: list[dict] = []  # conversation history

    # ── Key-value store ───────────────────────────────────────────────────────

    def set(self, key: str, value: Any) -> None:
        """Store a value under key."""
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value by key, returning default if not found."""
        return self._store.get(key, default)

    def delete(self, key: str) -> None:
        """Remove a key from the store."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all stored data and history."""
        self._store.clear()
        self._history.clear()

    def all(self) -> dict:
        """Return a copy of the full store."""
        return dict(self._store)

    # ── Conversation history ──────────────────────────────────────────────────

    def add_turn(self, role: str, content: str, agent: str = "") -> None:
        """
        Append a conversation turn to the history.

        Args:
            role:    "user" or "assistant".
            content: The message text.
            agent:   Which agent produced this turn (for assistant turns).
        """
        self._history.append({"role": role, "content": content, "agent": agent})

    def get_history(self, last_n: int = 10) -> list[dict]:
        """
        Return the last N conversation turns.

        Args:
            last_n: How many turns to return.

        Returns:
            List of turn dicts.
        """
        return self._history[-last_n:]

    def get_history_for_api(self, last_n: int = 10) -> list[dict]:
        """
        Return history formatted for the Claude API (role + content only).

        Args:
            last_n: How many turns to return.

        Returns:
            List of {"role": str, "content": str} dicts.
        """
        return [{"role": t["role"], "content": t["content"]} for t in self._history[-last_n:]]

    def history_length(self) -> int:
        """Return the number of stored turns."""
        return len(self._history)
