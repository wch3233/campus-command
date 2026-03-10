"""
main.py — Campus Command entry point.

Instantiates all agents, passes a goal/query to the orchestrator,
and runs the full agentic loop.

Usage:
    python main.py
    python main.py "What is the quadratic formula?"
    python main.py --interactive
"""

import sys
import os
import argparse
import json

# Ensure package root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import Orchestrator
from agents.agent_guidance_counsler import GuidanceCounslerAgent
from agents.agent_math import MathAgent
from agents.agent_science import ScienceAgent
from agents.agent_history import HistoryAgent
from agents.agent_ap_reader import APReaderAgent
from agents.agent_english import EnglishAgent
from agents.agent_literature import LiteratureAgent
from agents.agent_coping_coach import CopingCoachAgent
from agents.agent_tutor import TutorAgent
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from config import ANTHROPIC_API_KEY


# ── Banner ────────────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════╗
║           CAMPUS COMMAND — Your AI School Team           ║
║         Rockwall ISD • Freshman • AP • ADD-Friendly      ║
╚══════════════════════════════════════════════════════════╝

Agents available:
  📚 Guidance Counselor  |  ➕ Math Teacher      |  🔬 Science Teacher
  🏛️  History Teacher     |  📝 AP Reader         |  ✍️  English Teacher
  📖 Literature Teacher  |  🧠 Coping Coach      |  🎓 Personal Tutor

Type your question and press Enter. Type 'quit' to exit.
Type 'history' to see recent conversation. Type 'help' for tips.
""".strip()

HELP_TEXT = """
Tips for best results:
  • Be specific: "Explain photosynthesis step by step" beats "science help"
  • Mention your subject: "For my AP History class..."
  • Ask for practice: "Give me 3 practice problems on..."
  • Request flashcards: "Make flashcards for the Civil War causes"
  • Get coping help: "I can't focus on my essay, help"
  • AP essay feedback: "Score my APUSH DBQ: [paste essay]"
""".strip()


# ── Build agent registry ──────────────────────────────────────────────────────

def build_agents() -> dict:
    """Instantiate all subject agents and return a registry dict."""
    return {
        "guidance_counselor": GuidanceCounslerAgent(),
        "math":               MathAgent(),
        "science":            ScienceAgent(),
        "history":            HistoryAgent(),
        "ap_reader":          APReaderAgent(),
        "english":            EnglishAgent(),
        "literature":         LiteratureAgent(),
        "coping_coach":       CopingCoachAgent(),
        "tutor":              TutorAgent(),
    }


# ── Validation ────────────────────────────────────────────────────────────────

def validate_environment() -> bool:
    """Check that required environment variables are set."""
    if not (ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")):
        print("❌ ERROR: ANTHROPIC_API_KEY is not set.")
        print("   Export it with: export ANTHROPIC_API_KEY='your-key-here'")
        return False
    return True


# ── Single query mode ─────────────────────────────────────────────────────────

def run_single_query(orchestrator: Orchestrator, query: str) -> str:
    """
    Run one query through the orchestrator and return the response text.

    Args:
        orchestrator: Configured Orchestrator instance.
        query:        Student's question.

    Returns:
        Response string.
    """
    print(f"\n🔄 Processing: {query[:80]}{'...' if len(query) > 80 else ''}\n")

    result = orchestrator.run({"query": query})

    if result["status"] == "success":
        return result["output"]
    else:
        return f"⚠️  {result.get('output', 'Something went wrong. Please try again.')}"


# ── Interactive mode ──────────────────────────────────────────────────────────

def run_interactive(orchestrator: Orchestrator, stm: ShortTermMemory, ltm: LongTermMemory) -> None:
    """
    Run an interactive REPL loop for the student.

    Args:
        orchestrator: Configured Orchestrator instance.
        stm:          Short-term memory for this session.
        ltm:          Long-term persistent memory.
    """
    print(f"\n{BANNER}\n")

    # Load and display any remembered facts
    facts = ltm.all_facts()
    if facts:
        print("📋 Remembered from last time:")
        for k, v in list(facts.items())[:3]:
            print(f"   • {k}: {v}")
        print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 See you next time! Keep up the great work.")
            # Save session summary
            history_count = stm.history_length()
            if history_count > 0:
                ltm.add_session_summary(f"Session with {history_count} exchanges completed.")
            break

        if not user_input:
            continue

        # Built-in commands
        if user_input.lower() in ("quit", "exit", "bye"):
            print("\n👋 See you next time! Keep up the great work.")
            if stm.history_length() > 0:
                ltm.add_session_summary(f"Session ended by user after {stm.history_length()} exchanges.")
            break

        if user_input.lower() == "help":
            print(f"\n{HELP_TEXT}\n")
            continue

        if user_input.lower() == "history":
            turns = stm.get_history(last_n=6)
            if not turns:
                print("No conversation history yet.\n")
            else:
                print("\n--- Recent conversation ---")
                for t in turns:
                    role = "You" if t["role"] == "user" else f"  [{t.get('agent', 'AI')}]"
                    print(f"{role}: {t['content'][:120]}")
                print()
            continue

        if user_input.lower().startswith("remember "):
            # Allow student to store a fact: "remember my name is Alex"
            fact = user_input[9:].strip()
            ltm.set("student_note", fact)
            print(f"✅ Remembered: {fact}\n")
            continue

        # Add to short-term memory
        stm.add_turn("user", user_input)

        # Build context from recent history
        history_str = ""
        recent = stm.get_history(last_n=4)
        if len(recent) > 1:
            history_str = "\n".join(
                f"{'Student' if t['role'] == 'user' else 'AI'}: {t['content']}"
                for t in recent[:-1]
            )

        # Run through orchestrator
        result = orchestrator.run({
            "query": user_input,
            "context": ltm.context_summary(),
            "history": history_str,
        })

        output = result.get("output", "I'm not sure. Let me think about that differently.")
        print(f"\n🎓 Campus Command:\n{output}\n")

        # Save to memory
        stm.add_turn("assistant", output, agent=result.get("notes", ""))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    """Main entry point — parse args and run appropriate mode."""
    parser = argparse.ArgumentParser(
        description="Campus Command — High School AI Agent Team"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Single query to run (omit for interactive mode)",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Force interactive mode even with a query arg",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON result (single query mode only)",
    )

    args = parser.parse_args()

    # Validate environment
    if not validate_environment():
        sys.exit(1)

    # Build agents and orchestrator
    print("⚙️  Initializing Campus Command agents...")
    agents = build_agents()
    orchestrator = Orchestrator(agents=agents)
    stm = ShortTermMemory()
    ltm = LongTermMemory()
    print(f"✅ {len(agents)} agents ready.\n")

    # Run in appropriate mode
    if args.query and not args.interactive:
        # Single query mode
        result = orchestrator.run({"query": args.query})
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            output = result.get("output", "No response generated.")
            print(f"\n🎓 Campus Command:\n{output}\n")
            print(f"[Status: {result['status']} | Confidence: {result.get('confidence', '?')}%]")
    else:
        # Interactive mode
        run_interactive(orchestrator, stm, ltm)


if __name__ == "__main__":
    main()
