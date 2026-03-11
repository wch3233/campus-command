"""
agent_ap_reader.py — AP Reader / Exam Prep Agent.

Scores AP-style essays (DBQ, LEQ, FRQ, SAQ) using College Board rubrics,
provides exam strategy, and gives detailed feedback.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from tools.claude_api import call_claude
from tools.web_search import search, format_results
from config import STUDENT_PROFILE


SYSTEM_PROMPT = f"""
You are an experienced AP Reader and Exam Coach — you have scored real AP exams
for the College Board and know exactly what earns points.

{STUDENT_PROFILE}

Your specialties:
1. Score AP essays using official College Board rubrics
2. Explain WHY each point was earned or missed — be specific
3. Teach exam strategy: time management, skipping and returning, process of elimination
4. Help the student practice the exact skills tested on each AP exam
5. Decode AP question prompts — what is it REALLY asking?

AP subjects you cover:
- APUSH (DBQ, LEQ, SAQ)
- AP World History (DBQ, LEQ, SAQ)
- AP Language & Composition (rhetorical analysis, argument, synthesis)
- AP Literature (poetry, prose, open-ended essays)
- AP Biology, Chemistry, Physics (FRQs)
- AP Calculus (FRQs)
- AP Statistics (FRQs)
- AP Government (FRQs, SCOTUS cases)
- AP Psychology, AP Economics

When scoring an essay:
- List each rubric point explicitly
- Quote the student's text when praising or critiquing
- End with a total score and one priority improvement
- Use format: "Earned [X/Y points]. Here's why..."

Remember: ADD students benefit from immediate, specific feedback — no vague comments.
""".strip()


class APReaderAgent(BaseAgent):
    """AP Reader — scores AP essays and coaches exam strategy."""

    def __init__(self):
        """Initialize the AP Reader agent."""
        super().__init__(name="AP Reader")

    def run(self, input_data: dict) -> dict:
        """
        Score an AP essay or answer an AP strategy question.

        Args:
            input_data: {
                "query":   str — the essay text OR strategy question,
                "subject": str — AP subject (e.g., "APUSH", "AP Bio"),
                "type":    str — essay type (e.g., "DBQ", "LEQ", "FRQ"),
                "context": str — optional prompt text
            }

        Returns:
            Structured response dict.
        """
        query = input_data.get("query", "").strip()
        subject = input_data.get("subject", "AP")
        essay_type = input_data.get("type", "essay")
        context = input_data.get("context", "")
        do_search = input_data.get("search", False)

        if not query:
            return self._failure("No essay or question provided.", notes="Empty query.")

        self.log(f"AP Reader query ({subject} {essay_type}): {query[:80]}")

        try:
            # Always search College Board for current rubrics when grading AP work
            rubric_ref = ""
            search_subject = subject if subject != "AP" else (
                next((s for s in ["Human Geography", "English Language", "Biology",
                                  "Calculus", "Statistics", "World History", "US History"]
                      if s.lower() in query.lower() or s.lower() in context.lower()), "")
            )
            if search_subject:
                results = search(
                    f"AP {search_subject} {essay_type} scoring rubric guidelines site:apcentral.collegeboard.org"
                )
                if not results:
                    results = search(f"AP {search_subject} {essay_type} College Board scoring guide 2025 2026")
                if results:
                    rubric_ref = f"\n\nOfficial College Board Scoring Resources:\n{format_results(results)}"

            user_message = query
            if context:
                user_message = (
                    f"AP Subject: {subject}\n"
                    f"Essay Type: {essay_type}\n"
                    f"Prompt: {context}\n\n"
                    f"Student's Essay/Response:\n{query}"
                )
            user_message += rubric_ref

            response = call_claude(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_message,
                max_tokens=3000,
            )

            self.log("AP Reader response generated.")
            return self._success(
                output=response,
                confidence=91,
                notes=f"AP {subject} {essay_type} reviewed.",
            )

        except Exception as e:
            self.log(f"AP Reader error: {e}")
            return self._failure(output=f"AP Reader error: {e}", notes=str(e))
