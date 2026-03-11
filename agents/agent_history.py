"""
agent_history.py — History Teacher Agent.

Covers US History, World History, AP US History (APUSH),
AP World History, AP Government & Politics, and AP Human Geography.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from tools.claude_api import call_claude
from tools.web_search import search, format_results
from config import STUDENT_PROFILE


SYSTEM_PROMPT = f"""
You are a knowledgeable, engaging high school History & Social Studies Teacher.

{STUDENT_PROFILE}

Your teaching approach:
1. Tell history as a STORY — connect events to real people and motivations
2. Use the acronym PERSIA (Political, Economic, Religious, Social, Intellectual, Artistic) for analysis
3. Always provide dates and key figures — memory hooks help ADD students
4. For APUSH/AP World: teach the exam skills (DBQ, LEQ, SAQ) explicitly
5. Connect Texas history to broader US/world events when relevant
6. Use "cause → effect → significance" structure for events

Topics you cover:
- US History (colonial era through modern)
- AP US History (APUSH) — Period 1–9
- World History (ancient through contemporary)
- AP World History: Modern
- AP US Government & Politics
- AP Human Geography
- Texas History (Rockwall ISD curriculum)

For essay prompts: Help structure thesis, evidence, and analysis.
For DBQs: Walk through sourcing, contextualization, and argument.
""".strip()


class HistoryAgent(BaseAgent):
    """History Teacher — US History, World History, and AP Social Studies."""

    def __init__(self):
        """Initialize the History agent."""
        super().__init__(name="History Teacher")

    def run(self, input_data: dict) -> dict:
        """
        Answer a history question, explain an event, or help with an essay.

        Args:
            input_data: {"query": str, "context": str, "search": bool}

        Returns:
            Structured response dict.
        """
        query = input_data.get("query", "").strip()
        context = input_data.get("context", "")
        do_search = input_data.get("search", False)

        if not query:
            return self._failure("No history question provided.", notes="Empty query.")

        self.log(f"History query: {query[:100]}")

        try:
            extra = ""
            if do_search:
                # Detect AP subject from injected context, fall back to broad AP history search
                ap_hint = ""
                if "AP Human Geography" in context:
                    ap_hint = "AP Human Geography"
                elif "AP World History" in context:
                    ap_hint = "AP World History Modern"
                elif "AP US History" in context or "APUSH" in context:
                    ap_hint = "AP US History APUSH"
                elif "AP Government" in context:
                    ap_hint = "AP US Government Politics"
                else:
                    ap_hint = "AP History Social Studies"
                results = search(f"{ap_hint} {query} College Board site:apcentral.collegeboard.org")
                if not results:
                    results = search(f"{ap_hint} {query} College Board exam curriculum")
                if results:
                    extra = f"\n\nCollege Board AP Resources:\n{format_results(results)}"

            user_message = query
            if context:
                user_message = f"Context: {context}\n\nHistory question: {query}"
            user_message += extra

            response = call_claude(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_message,
            )

            self.log("History response generated.")
            return self._success(
                output=response,
                confidence=88,
                notes="History content provided.",
            )

        except Exception as e:
            self.log(f"History error: {e}")
            return self._failure(output=f"History agent error: {e}", notes=str(e))
