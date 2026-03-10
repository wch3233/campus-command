"""
agent_coping_coach.py — ADD Coping Coach Agent.

Provides evidence-based strategies for focus, organization, time management,
and academic stress specific to students with ADD/ADHD.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from tools.claude_api import call_claude
from config import STUDENT_PROFILE


SYSTEM_PROMPT = f"""
You are a compassionate, practical ADD/ADHD Coping Coach for high school students.

{STUDENT_PROFILE}

Your specialties:
1. Executive function strategies (planning, starting tasks, finishing tasks)
2. Focus techniques tailored for ADD brains (Pomodoro, body doubling, noise tips)
3. Study environment optimization (lighting, sound, fidgets, standing desks)
4. Breaking overwhelming assignments into micro-steps
5. Self-advocacy: how to talk to teachers about accommodations (IEP/504 plans)
6. Emotional regulation when frustrated with schoolwork

Your communication style:
- Ultra-short bullet points — never more than 3 sentences per idea
- Lead with action: "Try this right now:"
- Normalize ADD struggles: "This is very common for ADD brains, here's why..."
- Avoid lecturing — ask "What's getting in the way?" and listen first
- Celebrate effort, not just results

Common strategies you teach:
- The 2-Minute Rule (start anything for just 2 minutes)
- Chunking tasks into 15-minute blocks
- Color-coded planner systems
- The "brain dump" for clearing mental clutter before studying
- Transition rituals between tasks
- Using music/white noise strategically
- Phone-free study zones with timed breaks

IMPORTANT: You are a COACH, not a therapist or doctor.
For serious mental health concerns (anxiety, depression, crisis),
always say: "Please talk to a parent, your school counselor, or a doctor about this."
""".strip()


class CopingCoachAgent(BaseAgent):
    """ADD Coping Coach — focus strategies, organization, and academic coping skills."""

    def __init__(self):
        """Initialize the Coping Coach agent."""
        super().__init__(name="Coping Coach")

    def run(self, input_data: dict) -> dict:
        """
        Provide coping strategies for a specific challenge.

        Args:
            input_data: {
                "query":     str — the student's challenge or question,
                "challenge": str — category hint: "focus", "organization",
                                   "stress", "starting", "time"
            }

        Returns:
            Structured response dict.
        """
        query = input_data.get("query", "").strip()
        challenge = input_data.get("challenge", "")

        if not query:
            return self._failure("No challenge described.", notes="Empty query.")

        self.log(f"Coping coach query (challenge={challenge or 'general'}): {query[:100]}")

        try:
            user_message = query
            if challenge:
                user_message = f"Challenge type: {challenge}\n\nStudent says: {query}"

            response = call_claude(
                system_prompt=SYSTEM_PROMPT,
                user_message=user_message,
            )

            self.log("Coping coach response generated.")
            return self._success(
                output=response,
                confidence=85,
                notes="ADD coping strategies provided.",
            )

        except Exception as e:
            self.log(f"Coping coach error: {e}")
            return self._failure(output=f"Coping Coach error: {e}", notes=str(e))
