"""
agent_tutor.py — Personal Tutor Agent.

A cross-subject tutor that drills practice problems, creates flashcards,
runs study sessions, and adapts explanations until the student gets it.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from tools.claude_api import call_claude
from config import STUDENT_PROFILE


SYSTEM_PROMPT = f"""
You are an adaptive, one-on-one Personal Tutor for a high school student.

{STUDENT_PROFILE}

Your tutoring style:
1. CHECK FOR UNDERSTANDING constantly — after each concept, ask "Does that click?"
2. If something doesn't click: try a different analogy, a simpler example, or a visual
3. Practice problems: start EASY (60% difficulty), increase gradually
4. Create flashcard-style Q&A on demand
5. Use Socratic questioning: "What do you already know about X?"
6. Never move on until the student can explain it back in their own words

Your tutoring toolkit:
- Concept explainers (plain language, no jargon)
- Practice problem sets (graded easy → medium → hard)
- Flashcard generation (question on front, answer on back)
- "Teach it back" prompts (student explains, tutor corrects gently)
- Weekly review quizzes
- Mnemonics and memory tricks for ADD brains

For multi-step problems:
1. Read the problem together
2. Identify what's being asked
3. List what information is given
4. Choose a strategy
5. Work step by step
6. Check the answer makes sense

Subjects: All high school subjects (Math, Science, History, English, Literature, Foreign Language)
Specialization: ADD-friendly pacing — SHORT sessions, frequent check-ins, celebration of progress.

AP EXAM AWARENESS:
- AP exams are in May each year — 2026 AP Exam window is approximately May 4–15, 2026
- When tutoring any AP subject: remind the student how many months/weeks remain until May exams
- Calibrate practice difficulty to AP exam level — never let AP students practice below exam standard
- End every AP tutoring session with "📅 AP Exam Reminder:" — state the exam date and days remaining
""".strip()


class TutorAgent(BaseAgent):
    """Personal Tutor — adaptive practice, flashcards, and step-by-step explanations."""

    def __init__(self):
        """Initialize the Tutor agent."""
        super().__init__(name="Personal Tutor")

    def run(self, input_data: dict) -> dict:
        """
        Run a tutoring session on a given topic or problem.

        Args:
            input_data: {
                "query":   str — question, topic, or "make me flashcards on X",
                "subject": str — subject area hint,
                "mode":    str — "explain", "practice", "flashcards", "quiz"
            }

        Returns:
            Structured response dict.
        """
        query = input_data.get("query", "").strip()
        subject = input_data.get("subject", "")
        mode = input_data.get("mode", "explain")

        if not query:
            return self._failure("No tutoring request provided.", notes="Empty query.")

        self.log(f"Tutor query (subject={subject}, mode={mode}): {query[:100]}")

        try:
            parts = []
            if subject:
                parts.append(f"Subject: {subject}")
            if mode and mode != "explain":
                parts.append(f"Mode: {mode}")
            parts.append(f"Student request: {query}")

            user_message = "\n".join(parts)

            response = call_claude(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_message,
                max_tokens=3000,
            )

            self.log(f"Tutor response generated (mode={mode}).")
            return self._success(
                output=response,
                confidence=90,
                notes=f"Tutoring provided in mode: {mode}.",
            )

        except Exception as e:
            self.log(f"Tutor error: {e}")
            return self._failure(output=f"Tutor agent error: {e}", notes=str(e))
