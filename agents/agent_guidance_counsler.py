"""
agent_guidance_counsler.py — Guidance Counselor Agent.

Helps the student with academic planning, course selection,
college prep, study strategies, and emotional check-ins.
Also serves as the "entry point" router when the query is unclear.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from tools.claude_api import call_claude
from config import STUDENT_PROFILE


SYSTEM_PROMPT = f"""
You are a warm, encouraging high school Guidance Counselor at a Rockwall ISD school in Texas.

{STUDENT_PROFILE}

Your responsibilities:
1. Help the student plan their academic path and understand graduation requirements
2. Suggest which agent/teacher to ask for specific subjects
3. Provide emotional support and coping strategies for academic stress
4. Explain AP course expectations and college prep basics
5. Route unclear queries to the right specialist

Guidelines:
- Be warm, patient, and non-judgmental
- Use short paragraphs — the student has ADD, avoid walls of text
- Celebrate small wins enthusiastically
- If you're not the right resource, explicitly say "You should ask the [Subject] teacher about this"
- For mental health concerns, always recommend talking to a real school counselor or parent

You do NOT teach subject content. You help with the "big picture."
""".strip()


class GuidanceCounslerAgent(BaseAgent):
    """Guidance Counselor — academic planning, routing, and emotional support."""

    def __init__(self):
        """Initialize the Guidance Counselor agent."""
        super().__init__(name="Guidance Counselor")

    def run(self, input_data: dict) -> dict:
        """
        Provide guidance or route to the appropriate specialist.

        Args:
            input_data: {
                "query":   str — student's question,
                "context": str — optional extra context,
                "history": str — optional conversation history
            }

        Returns:
            Structured response dict.
        """
        query = input_data.get("query", "").strip()
        context = input_data.get("context", "")
        history = input_data.get("history", "")

        if not query:
            return self._failure("No query provided.", notes="Empty query received.")

        self.log(f"Received query: {query[:100]}")

        try:
            user_message = query
            if context:
                user_message = f"Context: {context}\n\nStudent's question: {query}"
            if history:
                user_message = f"Previous conversation:\n{history}\n\n{user_message}"

            response = call_claude(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_message,
            )

            self.log(f"Response generated ({len(response)} chars)")
            return self._success(
                output=response,
                confidence=88,
                notes="Guidance counselor response generated.",
            )

        except Exception as e:
            self.log(f"Error: {e}")
            return self._failure(
                output=f"I ran into a problem: {e}",
                notes=str(e),
            )
