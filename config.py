"""
config.py — Campus Command Configuration
All API keys are loaded from environment variables. Never hardcode secrets.
"""

import os

# ── API Keys ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
BRAVE_API_KEY: str = os.environ.get("BRAVE_API_KEY", "")
GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN", "")

# ── Model ─────────────────────────────────────────────────────────────────────
MODEL_NAME: str = "claude-sonnet-4-6"

# ── Agentic Loop Limits ───────────────────────────────────────────────────────
MAX_RETRIES: int = 3
MAX_ITERATIONS: int = 20

# ── Student Profile (injected into all agent system prompts) ──────────────────
STUDENT_PROFILE: str = """
STUDENT CONTEXT — read this carefully before every response:
- Grade: 9th Grade Freshman
- School: Rockwall ISD, Rockwall, Texas (Rockwall County)
- Challenges: ADD (Attention Deficit Disorder) — needs SHORT, chunked explanations
- Classes: Includes Advanced Placement (AP) courses
- Communication style: Be encouraging, use bullet points, avoid walls of text
- Pacing: Break everything into numbered steps. Ask "Does that make sense?" at natural stopping points.
- If confused: Restate the question, ask a clarifying question, then try a different approach
"""

# ── Log path ──────────────────────────────────────────────────────────────────
LOG_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "run_log.json")
