# CAMPUS COMMAND 🎓
**Your AI School Team — Powered by Claude**

A fully agentic AI assistant for high school students in Rockwall ISD, Texas.
Built for AP students with ADD — short answers, step-by-step help, real encouragement.

---

## Agent Roster

| Agent | What they do |
|---|---|
| 🎓 Guidance Counselor | Academic planning, routing, emotional check-ins |
| ➕ Math Teacher | Algebra → AP Calculus, step-by-step solutions |
| 🔬 Science Teacher | Biology, Chemistry, Physics, AP Sciences |
| 🏛️ History Teacher | APUSH, AP World, DBQ/LEQ coaching |
| 📝 AP Reader | Scores AP essays with College Board rubrics |
| ✍️ English Teacher | Writing, grammar, essay structure, AP Lang |
| 📖 Literature Teacher | Literary analysis, poetry, AP Lit |
| 🧠 Coping Coach | ADD strategies, focus, organization, stress |
| 🎯 Personal Tutor | Practice problems, flashcards, adaptive pacing |

---

## Setup

### 1. Install Python dependencies
```bash
cd campus-command
pip install -r requirements.txt
```

### 2. Set your API key
```bash
export ANTHROPIC_API_KEY="your-key-here"
```
Get a key at: https://console.anthropic.com

### Optional: Brave Search (for web search)
```bash
export BRAVE_API_KEY="your-brave-key"
```

### Optional: GitHub API (for code project help)
```bash
export GITHUB_TOKEN="your-github-token"
```

---

## Usage

### Interactive mode (recommended)
```bash
python main.py
```

### Single query
```bash
python main.py "What is the quadratic formula and how do I use it?"
python main.py "Help me outline an APUSH DBQ about industrialization"
python main.py "I can't focus on my homework, what should I do?"
```

### JSON output (for scripting)
```bash
python main.py --json "Explain photosynthesis step by step"
```

---

## Example Queries

```
# Math
"Solve 3x² - 5x + 2 = 0 step by step"
"What's the difference between mean, median, and mode?"
"How do I find the derivative of x³ + 2x?"

# Science
"Explain the steps of mitosis"
"What happens during a chemical reaction?"
"How does Newton's second law work?"

# History / APUSH
"What caused the Civil War? (give me 3 main causes)"
"Help me write a thesis for a DBQ about the New Deal"

# AP Essays
"Score my AP Lang rhetorical analysis: [paste essay]"
"What are the AP World History essay rubric points?"

# English / Writing
"My thesis is weak — help me strengthen it"
"What's the difference between a metaphor and a simile?"

# Literature
"What does the green light symbolize in The Great Gatsby?"
"Analyze this poem: [paste poem]"

# ADD & Focus
"I've been staring at this essay for an hour and can't start"
"How do I stay focused during a long test?"

# Flashcards & Practice
"Make me flashcards for the causes of World War I"
"Give me 5 practice problems on solving linear equations"
```

---

## Project Structure

```
campus-command/
├── agents/
│   ├── base_agent.py          # Abstract base class
│   ├── orchestrator.py        # Hub-and-spoke routing brain
│   ├── agent_guidance_counsler.py
│   ├── agent_math.py
│   ├── agent_science.py
│   ├── agent_history.py
│   ├── agent_ap_reader.py
│   ├── agent_english.py
│   ├── agent_literature.py
│   ├── agent_coping_coach.py
│   └── agent_tutor.py
├── tools/
│   ├── claude_api.py          # Anthropic API wrapper (streaming)
│   ├── web_search.py          # Brave Search + DuckDuckGo fallback
│   ├── browser_automation.py  # Page fetching + HTML stripping
│   ├── github_api.py          # GitHub repo search
│   └── spreadsheet___csv.py   # CSV read/write/stats
├── memory/
│   ├── short_term.py          # In-memory session storage
│   └── long_term.py           # JSON-persisted cross-session storage
├── logs/
│   └── run_log.json           # Timestamped agent activity log
├── config.py                  # API keys + constants
├── main.py                    # Entry point
└── requirements.txt
```

---

## How It Works

1. Student types a question
2. **Orchestrator** classifies the query using Claude and routes it
3. The right **subject agent** generates a response using Claude
4. If the agent fails, the orchestrator retries (up to 3×) or backtracks
5. If two agents are needed, their outputs are **synthesized** into one answer
6. The answer is displayed and logged
7. **Long-term memory** remembers facts across sessions

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | required | Your Anthropic API key |
| `BRAVE_API_KEY` | optional | Brave Search for web results |
| `GITHUB_TOKEN` | optional | GitHub API for code projects |
| `MODEL_NAME` | `claude-sonnet-4-6` | Claude model to use |
| `MAX_RETRIES` | `3` | Retries per failed step |
| `MAX_ITERATIONS` | `20` | Max agentic loop iterations |

---

## Built for
- **Rockwall ISD** freshman students
- **Advanced Placement** coursework
- Students with **ADD** — chunked, structured, encouraging responses
- Fully agentic — runs automatically once the question is asked
