"""
orchestrator.py — Campus Command Orchestrator.

Hub-and-spoke controller that:
  1. Classifies the student's query
  2. Delegates to the right subject-matter agent(s)
  3. Evaluates results and retries on failure
  4. Synthesizes a final answer
  5. Runs the full agentic loop with retry/backtrack logic
"""

import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent
from tools.claude_api import call_claude
from config import STUDENT_PROFILE, MAX_RETRIES, MAX_ITERATIONS, MODEL_NAME

# ── Routing prompt ─────────────────────────────────────────────────────────────
ROUTER_PROMPT = f"""
You are the routing brain of Campus Command, a high school AI assistant.

{STUDENT_PROFILE}

Given a student's query, classify it and return a JSON object with:
{{
  "primary_agent": "one of: guidance_counselor, math, science, history, ap_reader, english, literature, coping_coach, tutor",
  "secondary_agent": "optional second agent name or null",
  "subject": "brief subject label",
  "query_type": "homework | essay | concept | practice | emotional | planning | ap_exam | flashcards | other",
  "needs_search": true or false,
  "rephrased_query": "a clearer version of the query for the agent",
  "confidence": 0-100
}}

Routing rules:
- Math problems → math
- Science questions → science
- History/social studies → history
- AP essay scoring/feedback → ap_reader
- Writing/grammar/essay structure → english
- Novel/poem/story analysis → literature
- Focus, ADD, stress, organization → coping_coach
- Step-by-step tutoring, flashcards, practice → tutor
- Course selection, college, "what should I do" → guidance_counselor
- Unclear queries → guidance_counselor

Return ONLY valid JSON. No explanation text.
""".strip()

# ── Synthesis prompt ────────────────────────────────────────────────────────────
SYNTHESIS_PROMPT = f"""
You are the Campus Command final synthesizer.

{STUDENT_PROFILE}

You receive the outputs of one or two subject-matter agents.
Your job:
1. Combine the information into ONE clean, student-friendly response
2. Remove repetition
3. Keep it SHORT and scannable (bullets, numbers, headers)
4. End with: "💡 Quick tip:" and one memorable takeaway
5. If the agents disagreed or were uncertain, say "I'm not 100% sure — let's verify this"

Do NOT add new information. Only organize and clarify what the agents said.
""".strip()


class Orchestrator(BaseAgent):
    """
    Central orchestrator that routes queries, delegates to agents,
    evaluates results, and runs the full agentic loop.
    """

    def __init__(self, agents: dict):
        """
        Initialize the Orchestrator.

        Args:
            agents: Dict mapping agent names to agent instances.
                    Keys: guidance_counselor, math, science, history,
                           ap_reader, english, literature, coping_coach, tutor
        """
        super().__init__(name="Orchestrator")
        self.agents = agents

    # ── Core interface ────────────────────────────────────────────────────────

    def run(self, input_data: dict) -> dict:
        """
        Entry point: run the full agentic loop for a student query.

        Args:
            input_data: {"query": str, "context": str, "history": list}

        Returns:
            Structured response dict with the final synthesized answer.
        """
        return self.loop(input_data)

    # ── Agentic loop ──────────────────────────────────────────────────────────

    def loop(self, input_data: dict) -> dict:
        """
        Full agentic loop with retry and backtrack logic.

        Loop structure:
            while not goal_achieved and iterations < MAX_ITERATIONS:
                plan = orchestrator.plan(current_state)
                for step in plan:
                    result = delegate(step)
                    if success → advance
                    elif retries >= MAX_RETRIES → handle_failure
                    else → retry(step)
                iterations += 1

        Args:
            input_data: {"query": str, "context": str}

        Returns:
            Structured response dict.
        """
        query = input_data.get("query", "").strip()
        if not query:
            return self._failure("No query provided.", notes="Empty input.")

        self.log(f"=== New query: {query[:120]} ===")

        goal_achieved = False
        iterations = 0
        last_result = None
        consecutive_failures = 0

        current_state = {
            "query": query,
            "context": input_data.get("context", ""),
            "history": input_data.get("history", ""),
            "attempts": [],
        }

        while not goal_achieved and iterations < MAX_ITERATIONS:
            iterations += 1
            self.log(f"Iteration {iterations}/{MAX_ITERATIONS}")

            # 1. Plan
            plan = self.plan(current_state)
            if not plan:
                self.log("Planning failed — no steps generated.")
                break

            # 2. Execute plan steps
            step_success = False
            for step in plan:
                retries = 0
                result = None

                while retries <= MAX_RETRIES:
                    self.log(f"Delegating step '{step['agent']}' (attempt {retries + 1})")
                    result = self.delegate(step)

                    if result["status"] == "success":
                        step_success = True
                        consecutive_failures = 0
                        break
                    elif result["status"] == "needs_retry" and retries < MAX_RETRIES:
                        retries += 1
                        self.log(f"Retrying step (attempt {retries + 1})")
                    else:
                        # Failure or max retries exceeded
                        consecutive_failures += 1
                        self.log(f"Step failed: {result.get('notes', '')}")

                        # Backtrack after 2 consecutive failures
                        if consecutive_failures >= 2:
                            self.log("2 consecutive failures — escalating to Orchestrator fallback.")
                            result = self._fallback_response(current_state)
                            goal_achieved = True
                        break

                current_state["attempts"].append(result)
                last_result = result

                if goal_achieved:
                    break

            # 3. Evaluate
            if step_success and last_result:
                evaluation = self.evaluate(current_state, last_result)
                if evaluation["goal_achieved"]:
                    goal_achieved = True
                    self.log("Goal achieved — synthesizing final response.")

                    # Synthesize final answer
                    final = self._synthesize(current_state)
                    return self._success(
                        output=final,
                        confidence=evaluation.get("confidence", 85),
                        notes=f"Completed in {iterations} iteration(s).",
                    )

        # Max iterations or failure fallback
        if last_result and last_result.get("status") == "success":
            return self._success(
                output=last_result["output"],
                confidence=70,
                notes=f"Completed at iteration limit ({iterations}).",
            )

        return self._failure(
            output="I wasn't able to fully answer that. Could you rephrase or give more detail?",
            notes=f"Loop ended after {iterations} iterations without success.",
        )

    # ── Planning ──────────────────────────────────────────────────────────────

    def plan(self, state: dict) -> list[dict]:
        """
        Classify the query and build an execution plan.

        Args:
            state: Current state dict including "query".

        Returns:
            List of step dicts: [{"agent": str, "input": dict}, ...]
        """
        query = state["query"]
        context = state.get("context", "")
        history = state.get("history", "")

        self.log(f"Planning for: {query[:80]}")

        try:
            routing_input = f"Student query: {query}"
            if context:
                routing_input += f"\nContext: {context}"

            raw = call_claude(
                system_prompt=ROUTER_PROMPT,
                user_message=routing_input,
                max_tokens=512,
            )

            # Strip markdown code fences if present
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]

            routing = json.loads(clean.strip())

        except Exception as e:
            self.log(f"Routing error: {e}. Defaulting to guidance_counselor.")
            routing = {
                "primary_agent": "guidance_counselor",
                "secondary_agent": None,
                "rephrased_query": query,
                "needs_search": False,
                "query_type": "other",
            }

        steps = []
        primary = routing.get("primary_agent", "guidance_counselor")
        secondary = routing.get("secondary_agent")

        agent_input = {
            "query": routing.get("rephrased_query", query),
            "context": context,
            "history": history,
            "search": routing.get("needs_search", False),
        }

        steps.append({"agent": primary, "input": agent_input})

        if secondary and secondary != primary and secondary in self.agents:
            steps.append({"agent": secondary, "input": agent_input})

        self.log(f"Plan: primary={primary}, secondary={secondary or 'none'}")
        return steps

    # ── Delegation ────────────────────────────────────────────────────────────

    def delegate(self, step: dict) -> dict:
        """
        Route a step to the appropriate agent and run it.

        Args:
            step: {"agent": str, "input": dict}

        Returns:
            Agent's structured response dict.
        """
        agent_name = step.get("agent", "guidance_counselor")
        agent_input = step.get("input", {})

        agent = self.agents.get(agent_name)
        if not agent:
            self.log(f"Unknown agent '{agent_name}' — falling back to guidance_counselor.")
            agent = self.agents.get("guidance_counselor")

        try:
            result = agent.run(agent_input)
            self.log(f"Agent '{agent_name}' returned status={result['status']}")
            return result
        except Exception as e:
            self.log(f"Agent '{agent_name}' raised exception: {e}")
            return self._failure(
                output=f"Agent error: {e}",
                notes=f"Exception in agent '{agent_name}': {e}",
            )

    # ── Evaluation ────────────────────────────────────────────────────────────

    def evaluate(self, state: dict, result: dict) -> dict:
        """
        Evaluate whether the current result satisfies the goal.

        Args:
            state:  Current state including original query and attempts.
            result: Latest agent result.

        Returns:
            {"goal_achieved": bool, "confidence": int, "reason": str}
        """
        if result.get("status") != "success":
            return {"goal_achieved": False, "confidence": 0, "reason": "Non-success status."}

        output = result.get("output", "")
        if not output or len(str(output).strip()) < 20:
            return {"goal_achieved": False, "confidence": 30, "reason": "Output too short."}

        confidence = result.get("confidence", 80)
        self.log(f"Evaluation: goal_achieved=True, confidence={confidence}")
        return {"goal_achieved": True, "confidence": confidence, "reason": "Adequate response."}

    # ── Synthesis ─────────────────────────────────────────────────────────────

    def _synthesize(self, state: dict) -> str:
        """
        Combine all successful agent outputs into a final student-friendly answer.

        Args:
            state: Current state with "attempts" list.

        Returns:
            Synthesized response string.
        """
        attempts = state.get("attempts", [])
        successful = [a for a in attempts if a.get("status") == "success"]

        if not successful:
            return "I couldn't find a good answer. Let's try again — can you give me more detail?"

        if len(successful) == 1:
            return successful[0]["output"]

        # Multiple agents — synthesize
        agent_outputs = "\n\n---\n\n".join(
            f"Agent Output {i + 1}:\n{a['output']}"
            for i, a in enumerate(successful)
        )

        try:
            synthesized = call_claude(
                system_prompt=SYNTHESIS_PROMPT,
                user_message=(
                    f"Original question: {state['query']}\n\n"
                    f"Agent outputs to combine:\n{agent_outputs}"
                ),
                max_tokens=2000,
            )
            return synthesized
        except Exception as e:
            self.log(f"Synthesis error: {e}. Returning first result.")
            return successful[0]["output"]

    # ── Fallback ──────────────────────────────────────────────────────────────

    def _fallback_response(self, state: dict) -> dict:
        """
        Generate a graceful fallback when agents repeatedly fail.

        Args:
            state: Current state.

        Returns:
            Structured response dict.
        """
        query = state.get("query", "")
        try:
            fallback = call_claude(
                system_prompt=(
                    f"You are a helpful high school AI assistant. {STUDENT_PROFILE}\n"
                    "The specialized agents encountered errors. Do your best to answer directly."
                ),
                user_message=query,
            )
            return self._success(
                output=fallback,
                confidence=60,
                notes="Fallback orchestrator response used.",
            )
        except Exception as e:
            return self._failure(
                output="I'm having trouble right now. Please try rephrasing your question.",
                notes=f"Fallback also failed: {e}",
            )
