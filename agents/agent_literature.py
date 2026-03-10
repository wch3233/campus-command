"""
agent_literature.py — Literature Teacher Agent.

Covers literary analysis, reading comprehension, poetry, novels,
short stories, AP Literature & Composition, and Socratic seminar prep.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from tools.claude_api import call_claude
from tools.web_search import search, format_results
from config import STUDENT_PROFILE


SYSTEM_PROMPT = f"""
You are a passionate high school Literature Teacher who makes books come alive.

{STUDENT_PROFILE}

Your teaching approach:
1. Start with "What do you already know or feel about this?" — build on prior knowledge
2. Explain literary devices with vivid examples from the text
3. For poems: read it literally first, THEN dig into meaning
4. Connect themes to the student's own life experience (keeps ADD brains engaged)
5. Never spoil endings — guide with questions instead

Topics you cover:
- Literary analysis: theme, symbolism, character, setting, conflict, tone, mood
- Literary devices: metaphor, irony, foreshadowing, allusion, imagery, etc.
- Poetry: structure, sound devices, interpretation
- Fiction: novels, short stories, novellas
- Drama: Shakespeare, modern plays
- AP Literature & Composition: prose and poetry essays, open-ended questions
- Common texts: To Kill a Mockingbird, The Great Gatsby, 1984, Romeo & Juliet,
  The Crucible, Of Mice and Men, Lord of the Flies, and Texas ELAR standards

When analyzing:
- Use STEAL for character analysis (Speech, Thoughts, Effect, Actions, Looks)
- Use TP-CASTT for poetry (Title, Paraphrase, Connotation, Attitude, Shift, Theme, Title revisit)
- For AP Lit essays: help craft a defensible thesis with textual evidence

Remember: Students with ADD find discussion-style learning more engaging than lectures.
Ask questions. Invite their interpretation first.
""".strip()


class LiteratureAgent(BaseAgent):
    """Literature Teacher — literary analysis, poetry, novels, and AP Lit."""

    def __init__(self):
        """Initialize the Literature agent."""
        super().__init__(name="Literature Teacher")

    def run(self, input_data: dict) -> dict:
        """
        Help analyze literature, explain a poem, or discuss a novel.

        Args:
            input_data: {
                "query":  str — question or passage to analyze,
                "title":  str — book/poem title if relevant,
                "search": bool — whether to search for additional context
            }

        Returns:
            Structured response dict.
        """
        query = input_data.get("query", "").strip()
        title = input_data.get("title", "")
        do_search = input_data.get("search", False)

        if not query:
            return self._failure("No literature question provided.", notes="Empty query.")

        self.log(f"Literature query (title={title or 'N/A'}): {query[:100]}")

        try:
            extra = ""
            if do_search and title:
                results = search(f"{title} literary analysis themes symbols")
                if results:
                    extra = f"\n\nBackground resources:\n{format_results(results)}"

            user_message = query
            if title:
                user_message = f"Text/Work: {title}\n\nQuestion: {query}"
            user_message += extra

            response = call_claude(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_message,
                max_tokens=2500,
            )

            self.log("Literature response generated.")
            return self._success(
                output=response,
                confidence=88,
                notes=f"Literary analysis provided{' for ' + title if title else ''}.",
            )

        except Exception as e:
            self.log(f"Literature error: {e}")
            return self._failure(output=f"Literature agent error: {e}", notes=str(e))
