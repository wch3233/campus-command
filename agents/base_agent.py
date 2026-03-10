"""
base_agent.py — Abstract base class for all Campus Command agents.

Every agent inherits from BaseAgent and must implement run().
All agents return a standardized dict with status, output, confidence, and notes.
"""

import json
import os
import datetime
from abc import ABC, abstractmethod
from typing import Any

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_PATH


class BaseAgent(ABC):
    """
    Abstract base class for all subject-matter agents.

    Subclasses must implement run(input_data) and return a structured dict.
    """

    def __init__(self, name: str, tools: list = None):
        """
        Initialize the agent.

        Args:
            name: Human-readable agent name (e.g., "Math Teacher").
            tools: List of tool instances this agent can use.
        """
        self.name = name
        self.tools = tools or []
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        if not os.path.exists(LOG_PATH):
            with open(LOG_PATH, 'w') as f:
                import json; json.dump([], f)

    # ── Abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    def run(self, input_data: dict) -> dict:
        """
        Execute the agent's task.

        Args:
            input_data: Dict containing at minimum {"query": str}.
                        May also include {"context": str, "history": list}.

        Returns:
            Structured dict: {
                "status":     "success" | "failure" | "needs_retry",
                "output":     <result data>,
                "confidence": int 0-100,
                "notes":      str describing what happened
            }
        """

    # ── Logging ───────────────────────────────────────────────────────────────

    def log(self, message: str) -> None:
        """
        Append a timestamped log entry to logs/run_log.json.

        Args:
            message: Human-readable description of what happened.
        """
        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            try:
                with open(LOG_PATH, "r") as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                logs = []

            logs.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "agent": self.name,
                "message": message,
            })

            with open(LOG_PATH, "w") as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"[{self.name}] Log error: {e}")

    # ── Response helpers ──────────────────────────────────────────────────────

    def _success(self, output: Any, confidence: int = 85, notes: str = "") -> dict:
        """Build a success response."""
        self.log(f"SUCCESS — {notes or 'task complete'}")
        return {"status": "success", "output": output, "confidence": confidence, "notes": notes}

    def _failure(self, output: Any, confidence: int = 0, notes: str = "") -> dict:
        """Build a failure response."""
        self.log(f"FAILURE — {notes or 'unknown error'}")
        return {"status": "failure", "output": output, "confidence": confidence, "notes": notes}

    def _needs_retry(self, output: Any, confidence: int = 30, notes: str = "") -> dict:
        """Build a needs-retry response."""
        self.log(f"NEEDS_RETRY — {notes}")
        return {"status": "needs_retry", "output": output, "confidence": confidence, "notes": notes}
