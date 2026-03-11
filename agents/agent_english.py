"""
agent_english.py — English / Writing Teacher Agent.

Covers grammar, writing mechanics, essay structure, research papers,
AP Language & Composition, and SAT/ACT writing.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from tools.claude_api import call_claude
from tools.web_search import search, format_results
from config import STUDENT_PROFILE


SYSTEM_PROMPT = f"""
You are a skilled, supportive high school English & Writing Teacher.

{STUDENT_PROFILE}

Your teaching approach:
1. NEVER rewrite the student's work entirely — guide them to improve it themselves
2. Ask one question at a time when helping them brainstorm
3. Use the "sandwich" feedback model: praise → specific critique → encouragement
4. Explain grammar rules with examples, not just definitions
5. For essays: focus on thesis, evidence, analysis (TEA: Topic, Evidence, Analysis)

Topics you cover:
- Grammar and mechanics (punctuation, sentence structure, parts of speech)
- Paragraph structure (topic sentence, body, conclusion)
- Essay types: expository, persuasive, narrative, analytical
- Research papers: thesis, citations (MLA/APA), avoiding plagiarism
- AP Language & Composition: rhetorical analysis, synthesis, argument essays
- SAT/ACT writing section prep
- College application essays

When reviewing writing:
1. Identify 2-3 specific strengths first
2. Point to ONE main improvement area
3. Show a corrected example, then ask the student to try the next sentence themselves

Remember: Students with ADD often have great ideas but struggle with organization.
Help them outline BEFORE they draft.
""".strip()


class EnglishAgent(BaseAgent):
    """English Teacher — writing, grammar, essays, and AP Language."""

    def __init__(self):
        """Initialize the English agent."""
        super().__init__(name="English Teacher")

    def run(self, input_data: dict) -> dict:
        """
        Help with writing, grammar, or essay structure.

        Args:
            input_data: {
                "query":   str — question or text to review,
                "task":    str — "review", "grammar", "outline", "brainstorm",
                "context": str — assignment prompt if available
            }

        Returns:
            Structured response dict.
        """
        query = input_data.get("query", "").strip()
        task = input_data.get("task", "general")
        context = input_data.get("context", "")
        do_search = input_data.get("search", False)

        if not query:
            return self._failure("No writing or question provided.", notes="Empty query.")

        self.log(f"English query (task={task}): {query[:100]}")

        try:
            extra = ""
            if do_search:
                if "AP Language" in context or "AP English" in context or "AP Lit" in context:
                    ap_hint = "AP English Literature" if "AP Lit" in context else "AP English Language Composition"
                    results = search(f"{ap_hint} {query} College Board rubric site:apcentral.collegeboard.org")
                    if not results:
                        results = search(f"{ap_hint} {query} College Board FRQ rhetorical analysis")
                else:
                    results = search(f"high school English writing {query} Texas TEKS")
                if results:
                    extra = f"\n\nCollege Board English Resources:\n{format_results(results)}"

            user_message = query
            if context:
                user_message = f"Assignment prompt: {context}\n\nStudent's work or question:\n{query}"
            if task and task != "general":
                user_message = f"Task type: {task}\n\n{user_message}"
            user_message += extra

            response = call_claude(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_message,
                max_tokens=2500,
            )

            self.log("English response generated.")
            return self._success(
                output=response,
                confidence=89,
                notes=f"English assistance provided (task: {task}).",
            )

        except Exception as e:
            self.log(f"English error: {e}")
            return self._failure(output=f"English agent error: {e}", notes=str(e))
