"""
agent_science.py — Science Teacher Agent.

Covers Biology, Chemistry, Physics, Environmental Science,
AP Biology, AP Chemistry, AP Physics 1/2/C, and AP Environmental Science.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from tools.claude_api import call_claude
from tools.web_search import search, format_results
from config import STUDENT_PROFILE


SYSTEM_PROMPT = f"""
You are an enthusiastic, clear high school Science Teacher.

{STUDENT_PROFILE}

Your teaching approach:
1. Explain the concept BEFORE diving into details
2. Use real-world analogies (e.g., "mitochondria are like power plants")
3. For calculations, show every step with units
4. Highlight key vocabulary in **bold**
5. Use numbered lists for processes (like cell division steps)
6. Connect concepts to Texas/local examples when relevant

Topics you cover:
- Biology: cells, genetics, evolution, ecology, AP Biology
- Chemistry: atoms, bonding, reactions, stoichiometry, AP Chemistry
- Physics: mechanics, waves, electricity, AP Physics 1/2/C
- Environmental Science: ecosystems, climate, AP Environmental Science
- Earth Science: geology, weather, astronomy

Lab reports: Help structure hypothesis, methods, results, and conclusion.
Texas TEKS standards are your curriculum guide.

IMPORTANT: Use LaTeX notation for all equations and formulas: $...$ for inline math and $$...$$ for block equations.
""".strip()


class ScienceAgent(BaseAgent):
    """Science Teacher — Biology, Chemistry, Physics, and AP Sciences."""

    def __init__(self):
        """Initialize the Science agent."""
        super().__init__(name="Science Teacher")

    def run(self, input_data: dict) -> dict:
        """
        Answer a science question or explain a science concept.

        Args:
            input_data: {"query": str, "context": str, "search": bool}

        Returns:
            Structured response dict.
        """
        query = input_data.get("query", "").strip()
        context = input_data.get("context", "")
        do_search = input_data.get("search", False)

        if not query:
            return self._failure("No science question provided.", notes="Empty query.")

        self.log(f"Science query: {query[:100]}")

        try:
            extra = ""
            if do_search:
                results = search(f"high school science {query}")
                if results:
                    extra = f"\n\nAdditional reference material:\n{format_results(results)}"

            user_message = query
            if context:
                user_message = f"Context: {context}\n\nScience question: {query}"
            user_message += extra

            response = call_claude(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_message,
            )

            self.log("Science response generated.")
            return self._success(
                output=response,
                confidence=90,
                notes="Science concept explained.",
            )

        except Exception as e:
            self.log(f"Science error: {e}")
            return self._failure(output=f"Science agent error: {e}", notes=str(e))
