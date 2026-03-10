"""
agent_math.py — Math Teacher Agent.

Covers Pre-Algebra, Algebra I/II, Geometry, Pre-Calculus,
AP Calculus AB/BC, and AP Statistics.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from tools.claude_api import call_claude
from tools.web_search import search, format_results
from config import STUDENT_PROFILE


SYSTEM_PROMPT = f"""
You are an expert, patient high school Math Teacher.

{STUDENT_PROFILE}

Your teaching approach:
1. ALWAYS show the step-by-step work — never just give the answer
2. Use plain language; avoid jargon unless you define it first
3. After solving a problem, offer a similar practice problem
4. Use analogies and real-world examples (sports scores, money, pizza)
5. Keep each step SHORT — one idea per bullet

Topics you cover:
- Pre-Algebra, Algebra I & II
- Geometry (proofs, theorems, coordinate geometry)
- Pre-Calculus & Trigonometry
- AP Calculus AB and BC (limits, derivatives, integrals)
- AP Statistics (distributions, inference, regression)

If the student seems frustrated, say: "Let's slow down and try a different way."
If a problem requires a calculator, say so and show the setup.
""".strip()


class MathAgent(BaseAgent):
    """Math Teacher — step-by-step math help from Algebra to AP Calculus."""

    def __init__(self):
        """Initialize the Math agent."""
        super().__init__(name="Math Teacher")

    def run(self, input_data: dict) -> dict:
        """
        Solve a math problem or explain a math concept.

        Args:
            input_data: {"query": str, "context": str, "search": bool}

        Returns:
            Structured response dict.
        """
        query = input_data.get("query", "").strip()
        context = input_data.get("context", "")
        do_search = input_data.get("search", False)

        if not query:
            return self._failure("No math question provided.", notes="Empty query.")

        self.log(f"Math query: {query[:100]}")

        try:
            extra = ""
            if do_search:
                results = search(f"high school math {query}")
                if results:
                    extra = f"\n\nAdditional reference material:\n{format_results(results)}"

            user_message = query
            if context:
                user_message = f"Additional context: {context}\n\nMath question: {query}"
            user_message += extra

            response = call_claude(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_message,
            )

            self.log("Math response generated.")
            return self._success(
                output=response,
                confidence=92,
                notes="Math solution provided with steps.",
            )

        except Exception as e:
            self.log(f"Math error: {e}")
            return self._failure(output=f"Math agent error: {e}", notes=str(e))
