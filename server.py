"""
server.py — Campus Command Flask API server.
Wraps all agents behind a REST API for the Electron UI.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
from memory.long_term import LongTermMemory
from tools.claude_api import call_claude_with_image

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

app = Flask(__name__, static_folder=DIST_DIR, static_url_path="")
CORS(app)


@app.route("/")
def serve_index():
    """Serve the React app for browser access."""
    return send_from_directory(DIST_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    """Serve static assets; fall back to index.html for client-side routing."""
    full = os.path.join(DIST_DIR, path)
    if os.path.isfile(full):
        return send_from_directory(DIST_DIR, path)
    return send_from_directory(DIST_DIR, "index.html")

agents = {
    "guidance_counselor": GuidanceCounslerAgent(),
    "math": MathAgent(),
    "science": ScienceAgent(),
    "history": HistoryAgent(),
    "ap_reader": APReaderAgent(),
    "english": EnglishAgent(),
    "literature": LiteratureAgent(),
    "coping_coach": CopingCoachAgent(),
    "tutor": TutorAgent(),
}
orchestrator = Orchestrator(agents=agents)
ltm = LongTermMemory()


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


@app.route('/api/network-url', methods=['GET'])
def network_url():
    """Return the local network URL so the UI can display it for other devices."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = None
    return jsonify({"url": f"http://{ip}:5001" if ip else None})


@app.route('/api/memory', methods=['GET'])
def get_memory():
    """Return all stored student facts."""
    return jsonify(ltm.all_facts())


@app.route('/api/memory', methods=['POST'])
def set_memory():
    """Save or update a student fact. Body: {"key": str, "value": str}"""
    data = request.json or {}
    key = data.get('key', '').strip()
    value = data.get('value', '').strip()
    if not key:
        return jsonify({"error": "key required"}), 400
    if value:
        ltm.set(key, value)
    else:
        ltm.delete(key)
    return jsonify({"status": "ok", "key": key, "value": value})


@app.route('/api/memory/delete', methods=['POST'])
def delete_memory():
    """Delete a stored fact. Body: {"key": str}"""
    data = request.json or {}
    key = data.get('key', '').strip()
    if key:
        ltm.delete(key)
    return jsonify({"status": "ok"})


_SCHEDULE_KEYWORDS = {"schedule", "class", "classes", "courses", "semester", "period", "my schedule"}

_SCHEDULE_EXTRACT_PROMPT = (
    "You are a class schedule parser. Look at this image and extract the student's class names. "
    "Return ONLY a comma-separated list of class names, nothing else. "
    "Example: 'Algebra I, English I Honors, AP Human Geography, Biology, PE, World Geography' "
    "If this is NOT a class schedule, return exactly: NOT_A_SCHEDULE"
)


def _maybe_extract_schedule(image_data: dict, query: str) -> None:
    """If the image looks like a class schedule, extract and save classes to memory."""
    q_lower = query.lower()
    if not any(kw in q_lower for kw in _SCHEDULE_KEYWORDS):
        return
    try:
        result = call_claude_with_image(
            system_prompt=_SCHEDULE_EXTRACT_PROMPT,
            user_message="Extract the class names from this schedule image.",
            image_base64=image_data["data"],
            media_type=image_data.get("type", "image/jpeg"),
            max_tokens=200,
        )
        extracted = result.strip()
        if extracted and extracted != "NOT_A_SCHEDULE" and len(extracted) > 4:
            ltm.set("current_classes", extracted)
            ltm.set("schedule_uploaded", "yes")
            print(f"[server] Schedule extracted and saved: {extracted[:80]}")
    except Exception as e:
        print(f"[server] Schedule extraction error: {e}")


@app.route('/api/query', methods=['POST'])
def query():
    data = request.json or {}
    query_text = data.get('query', '').strip()
    context = data.get('context', '')
    image_data = data.get('image')  # optional: {"data": base64str, "type": "image/jpeg"}

    if not query_text and not image_data:
        return jsonify({"status": "failure", "output": "No query provided.", "confidence": 0, "notes": ""}), 400

    # Inject student profile facts into every query
    memory_ctx = ltm.context_summary()
    if memory_ctx and memory_ctx != "No long-term context stored yet.":
        context = f"{memory_ctx}\n\n{context}" if context else memory_ctx

    # Inject recent conversation history
    history = ltm.format_history_for_prompt(last_n=6)

    # If image looks like a schedule, auto-extract classes before responding
    if image_data and image_data.get("data"):
        _maybe_extract_schedule(image_data, query_text)

    # Save the student's turn to conversation history
    ltm.add_conversation_turn("user", query_text or "[image uploaded]")

    result = orchestrator.run({
        "query": query_text,
        "context": context,
        "history": history,
        "image": image_data,
    })

    # Save the assistant's response turn
    if result.get("status") == "success":
        agent_label = result.get("notes", "assistant")
        ltm.add_conversation_turn("assistant", result.get("output", ""), agent=agent_label)

    return jsonify(result)


if __name__ == '__main__':
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "your-mac-ip"
    print("=" * 55)
    print("  Campus Command server starting...")
    print(f"  Local (this Mac):  http://localhost:5001")
    print(f"  Network (browser): http://{local_ip}:5001")
    print("=" * 55)
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
