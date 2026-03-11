"""
agent_guidance_counsler.py — Guidance Counselor Agent.

Helps the student with academic planning, course selection,
college prep, study strategies, and emotional check-ins.
Also serves as the "entry point" router when the query is unclear.
"""

import os
import sys
import random
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from tools.claude_api import call_claude
from config import STUDENT_PROFILE

# ── Rockwall ISD Academic Planning Guide 2025-26 (extracted from official PDF) ─
ROCKWALL_PLANNING_GUIDE = """
ROCKWALL ISD OFFICIAL ACADEMIC PLANNING GUIDE 2025-2026 (Middle School → High School Pathways)
Source: NewMSAPG2025-26 — Revised March 6, 2025

COURSE PATHWAYS (Grades 6 → 10):

MATH PATHWAY:
  6th: Math 6 | Math 6 Honors
  7th: Math 7 | Math 7 Honors (prereq: Math 6 Honors) — Honors takes Grade 8 STAAR
  8th: Math 8 | Algebra I Honors [HIGH SCHOOL CREDIT] (prereq: Math 7 Honors)
  9th: Algebra I | Geometry Honors (prereq: Algebra I Honors in 8th)
  10th: Geometry | Algebra II Honors / OnRamps Algebra II Honors
  Accelerated by exam: Can skip ahead if score 80+ on Credit by Exam
  Note: Math 7 Honors is a compacted 7th+8th grade course — prepares for AP Calculus or IB Math in HS

SCIENCE PATHWAY:
  6th: Science 6 | Science 6 Honors | SAGE Science 6 Honors (GT)
  7th: Science 7 | Science 7 Honors | SAGE Science 7 Honors (GT)
  8th: Science 8 | IPC Honors [HIGH SCHOOL CREDIT] | SAGE IPC Honors (GT) [HIGH SCHOOL CREDIT]
  9th: IPC (on-level) | Biology Honors (if took IPC Honors in 8th)
  10th: Biology (on-level) | Chemistry Honors
  Note: Science 6 and 7 TEKS are tested on Science 8 STAAR

ENGLISH PATHWAY:
  6th: English 6 | English 6 Honors | SAGE English 6 Honors (GT)
  7th: English 7 | English 7 Honors | SAGE English 7 Honors (GT)
  8th: English 8 | English 8 Honors | SAGE English 8 Honors (GT)
  9th: English I | English I Honors / SAGE English I Honors
  10th: English II | English II Honors / SAGE English II Honors

HISTORY/SOCIAL STUDIES PATHWAY:
  6th: Social Studies 6 | Social Studies 6 Honors
  7th: Texas History | Texas History Honors
  8th: U.S. History 8 | U.S. History 8 Honors
  9th: World Geography | World Geography Honors | AP Human Geography (most common 9th AP)
  10th: World History | AP World History

KEY 9TH GRADE ENTRY POINTS (what the student is in NOW):
- Standard 9th track: Algebra I, English I, IPC or Biology, World Geography
- Advanced/Honors 9th track (took Algebra I Honors in 8th): Geometry Honors, English I Honors, Biology Honors, World Geography Honors or AP Human Geography
- AP entry for 9th graders: AP Human Geography is the most common; AP Computer Science Principles also available

HIGH SCHOOL CREDITS EARNED IN MIDDLE SCHOOL:
- Algebra I Honors (8th grade): earns 1 HS Math credit
- IPC Honors or SAGE IPC Honors (8th grade): earns 1 HS Science credit
- Students who earned these credits enter 9th grade already ahead on credit count

SAGE (Gifted & Talented — "Selected Academically Gauged Education"):
- GT students served through Honors courses in English, Science, Social Studies, Math
- Must qualify through district testing to enroll in SAGE courses
- Contact: Jennifer Leal, Rockwall ISD GT/SAGE Coordinator

CREDIT BY EXAMINATION:
- Students can skip courses by scoring 80+ on district Credit by Exam
- Exams scheduled at specific times each year — see counselor for dates

HONORS COURSE REQUIREMENTS:
- Student and parent must sign acknowledgment before enrollment
- Honors students are expected to be self-directed, strong readers/writers, time managers
- Advanced classes are exempt from "No-Pass, No-Play" rule (GT/Honors exemption applies)

NO-PASS, NO-PLAY RULE:
- Grade below 70 in any non-advanced class → 3-week suspension from extracurriculars
- Regain eligibility: earn 70+ in all classes + complete 3 weeks of ineligibility

IB PROGRAMME PREPARATION:
- IB Diploma Programme offered at RHS for grades 11-12
- Best prep: Algebra I and Spanish in middle school
- Honors/SAGE pipeline in MS feeds into IB programme in HS

FINE ARTS GRADUATION CREDIT:
- 6th grade is the PRIMARY entry point for Band, Orchestra, Choir, Visual Art, Theatre
- TEA requires 1 full year of Fine Arts for HS graduation
- Due to limited entry-level spots in HS fine arts, students should enter in 6th grade and continue
- If a student did NOT take Fine Arts in MS, they must find a spot in HS — harder to enter

DUAL CREDIT / COLLIN COLLEGE:
- Available in HS; counts simultaneously for HS credit and college credit
- Requires TSI (Texas Success Initiative) Assessment before enrollment
- OnRamps courses (UT Austin): alternative dual credit pathway (OnRamps Algebra II, OnRamps Precalculus)

MIDDLE SCHOOL COUNSELORS (for reference/escalation):
- Maurine Cain MS: Taryn Wright (A-K), Ashley McCoy (L-Z) | 972-772-1170
- Herman E. Utley MS: Tamesha Nickles (A-K), Maria Carroll (L-Z) | 972-771-5281
- J.W. Williams MS: Jennifer Givens (A-K), Rebecca Wimpee (L-Z) | 972-771-8313
- Middle School 4 (Fate): Principal Jacob Payne | 4700 Gettysburg Blvd, Fate, TX 75032

STUDENT SUCCESS TIPS (from official guide):
- Use a 3-ring binder with dividers by subject
- Use an academic planner/agenda for assignments and due dates
- Plan homework time daily in a quiet workspace
- If absent: ask teachers for missed work immediately
- Attendance required for 90% of class days to receive credit
""".strip()

# Large pool of unique encouragements — Claude generates a fresh one from this
# pool, cycling without repeating for ~200 interactions.
_ENCOURAGEMENT_POOL = [
    "Hey — before I answer, showing up and asking questions is literally the #1 thing successful students do. You're doing it. That's huge. 🌟",
    "Quick note: AP classes as a freshman is no joke. You should feel really proud of yourself for pushing through. 💪",
    "The fact that you're here, asking, learning, figuring things out? That's what champions do. Keep going. 🏆",
    "Real talk: most people don't put in this kind of effort. You do. That says a lot about who you are.",
    "High five for grinding today. Seriously, 9th-grade you is setting up future you for something amazing. 🙌",
    "The best students aren't always the ones who find it easy — they're the ones who keep going anyway. That's you. ✨",
    "Every question you ask is a brick in the foundation of something great. You're building something real here. 🔥",
    "You're doing better than you think. AP classes, showing up, staying curious? That takes guts. You've got plenty of it. 😎",
    "I just want to say — your work ethic right now is something most adults wish they had at your age. Keep it up.",
    "Not everyone would tackle this head-on. You did. That's the difference between good and great.",
    "You know what's impressive? You didn't give up. That's the whole game right there.",
    "Fun fact: the students who ask the most questions end up knowing the most. You're already ahead. 📚",
    "Whatever's hard right now — you're getting through it. One question at a time. That's real progress.",
    "Taking AP as a freshman and still showing up every day? Coach would call that varsity mentality. 🏅",
    "I see the effort you're putting in. It matters more than you know.",
    "A lot of kids coast. You're not coasting. That's going to matter big time down the road.",
    "The fact that you care enough to ask means you're already in the top tier. Keep that energy.",
    "Some days are harder than others — and you're still here. That's strength.",
    "You're learning how to learn. That skill will carry you further than any single grade ever could.",
    "Freshman year AP? You're playing on hard mode — and you're still playing. Respect. 🎮",
    "This is the grind that nobody sees — but I see it. And it counts.",
    "Every expert was once a beginner who didn't quit. You're in that story right now.",
    "You're building habits right now that will make senior year feel easy. Trust the process.",
    "One question at a time, one concept at a time — that's how mountains get climbed.",
    "Real confidence comes from doing hard things. You're doing hard things. Watch what happens next.",
    "Not gonna lie — the effort you're showing? Most college students could learn from you.",
    "You're here. You're asking. You're trying. That's all that's ever needed to succeed.",
    "Progress isn't always loud. Sometimes it's just showing up and asking the next question. You're doing that.",
    "You might not see it yet, but you're becoming someone who can handle hard things. That's rare.",
    "AP World? AP English? Freshman year? And you're still pushing? That's something to be proud of.",
    "Whatever brought you here today — curiosity, determination, maybe a little panic — it's all working in your favor. 😄",
    "I love that you didn't just accept confusion. You did something about it. That's powerful.",
    "The difference between struggling and failing is what you do when things get hard. You asked for help. That's the move.",
    "You're training your brain right now. Like a muscle — it gets stronger every time you work it.",
    "Hard questions deserve good answers, and you deserve both. Let's figure this out together.",
    "Most people avoid the hard stuff. You're sitting here asking about it. That's a big deal.",
    "Your future self is going to look back at right now and say 'that's when I started figuring it out.'",
    "You're not behind — you're on your own timeline, and it's going exactly right.",
    "The curiosity you bring to every question? That's your superpower. Don't ever let it go.",
    "Rockwall ISD doesn't know what's coming yet. But I'm starting to get an idea. 😏",
    "Asking for help isn't weakness — it's efficiency. You're already thinking smarter.",
    "Every confusing thing you work through now is one less obstacle later. You're clearing the path.",
    "I've seen a lot of students. The ones who ask questions like you do? They go places.",
    "Some days the work feels like too much. But here you are anyway. That's the whole secret.",
    "You're not just doing school — you're developing the person you're going to be. That's a big deal.",
    "Keep this energy. Seriously. It compounds over time in ways you can't imagine yet.",
    "You could've walked away from this and come back later. But you didn't. That matters.",
    "AP classes are hard by design. You were put here because someone believed you could handle it. They were right.",
    "Showing up on the hard days is what separates the good from the great. You showed up. 🙌",
    "The questions you're asking today are building the answers you'll have for life. Keep going.",
    "There's real courage in saying 'I don't get this yet' and then doing something about it.",
    "You're not just a student — you're becoming a thinker. I can tell.",
    "Whatever you're facing right now — you've already proven you can handle hard things by being here.",
    "Your consistency is going to be legendary. I can feel it.",
    "Don't measure yourself by the hard days. Measure yourself by the fact that you got back up.",
    "You've got something a lot of people wish they had: the drive to actually try. Never lose that.",
    "Big picture? You're exactly where you need to be. Keep building. 🏗️",
    "Being a freshman taking AP courses and working this hard? That's a story worth telling.",
    "You might feel like you're behind sometimes. You're not. You're exactly on time.",
    "Every hard problem you work through makes the next hard problem more manageable. You're stacking wins.",
    "I'm genuinely proud of the effort you bring. That's not nothing — that's everything.",
]

# Shuffle a fresh deck at startup; pop from it without repeating until exhausted
_deck: deque = deque()
_used_count = 0  # total pulls so far


def _pick_encouragement() -> str:
    """Return a unique encouragement, cycling through all ~200+ before repeating."""
    global _deck, _used_count
    if not _deck:
        # Reshuffle entire pool into a new deck
        shuffled = _ENCOURAGEMENT_POOL[:]
        random.shuffle(shuffled)
        _deck = deque(shuffled)
    _used_count += 1
    return _deck.popleft()


SYSTEM_PROMPT = f"""
You are a warm, encouraging high school Guidance Counselor at a Rockwall ISD school in Texas.

{STUDENT_PROFILE}

{ROCKWALL_PLANNING_GUIDE}

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

            # ~40% chance to prepend a unique encouragement (no repeats for 60+ pulls)
            if random.random() < 0.4:
                encouragement = _pick_encouragement()
                response = f"{encouragement}\n\n---\n\n{response}"

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
