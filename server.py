"""
server.py — Campus Command Flask API server.
Wraps all agents behind a REST API for the Electron UI.
"""

from flask import Flask, request, jsonify
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

app = Flask(__name__)
CORS(app)

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


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


@app.route('/api/query', methods=['POST'])
def query():
    data = request.json or {}
    query_text = data.get('query', '').strip()
    context = data.get('context', '')
    history = data.get('history', '')
    if not query_text:
        return jsonify({"status": "failure", "output": "No query provided.", "confidence": 0, "notes": ""}), 400
    result = orchestrator.run({"query": query_text, "context": context, "history": history})
    return jsonify(result)


if __name__ == '__main__':
    print("Campus Command API server starting on port 5001...")
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
