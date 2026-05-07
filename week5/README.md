# Week 5 — Agent Architecture with LLM Tool Use

## Overview

This week you'll build an AI agent that answers TechCorp business questions by combining an LLM with database queries and document retrieval. The agent will:

- Use Gemini 2.5 Pro to reason about which tools to call
- Query the TechCorp SQLite database (employees, policies, expenses)
- Track API costs and enforce access control
- Handle errors gracefully

**Key concept:** Agents chain together LLM reasoning + tool execution. The LLM decides which tools to call, you handle the results, then synthesize an answer.

---

## Setup (15 minutes)

### 1. Get a Google AI API Key

Visit [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) and generate a free API key.

```bash
# Set as environment variable
export GOOGLE_API_KEY="AIza..."

# Or create .env file in week5/
echo "GOOGLE_API_KEY=AIza..." > week5/.env
```

### 2. Install Dependencies

```bash
cd week5
pip install -r requirements.txt
```

**Required packages:**

- `google-genai` - Google's Gemini API
- `fastapi` + `uvicorn` - Web framework
- `pytest` - Testing

---

## Your Tasks

### 1. Define Tools (30 min)

Open `app/agent.py` and implement the `Tool` base class and 3 specific tools:

```python
class Tool:
    """Base tool class."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
  
    def execute(self, **kwargs) -> str:
        # TODO: implement
        raise NotImplementedError

class EmployeeLookupTool(Tool):
    """Look up employee by name or ID."""
    # TODO: implement execute() to query SQLite employees table

class PolicySearchTool(Tool):
    """Search policy documents."""
    # TODO: implement execute() to search documents by keyword

class ExpenseQueryTool(Tool):
    """Query expense policies and limits."""
    # TODO: implement execute() to look up expense rules
```

### 2. Build the Agent (45 min)

Implement the `Agent` class:

```python
class Agent:
    def __init__(self, db_path: str, api_key: str = None):
        # TODO: initialize Google GenAI client with api_key
        # TODO: load tools
        # TODO: set up token tracking
        pass
  
    def query(self, user_query: str, user_role: str = "engineer") -> Dict:
        """Answer a question using LLM + tools."""
        # TODO: build system prompt describing available tools
        # TODO: call LLM with user_query
        # TODO: parse LLM response, identify which tools to call
        # TODO: execute tools
        # TODO: synthesize answer from tool results
        # TODO: track tokens and cost
        return {
            "answer": "...",
            "tokens_used": 0,
            "cost": 0.0
        }
```

**How the reasoning loop works:**

1. You build a prompt describing the tools: "You have access to tools: ..."
2. Pass user question to Gemini
3. Gemini responds with reasoning: "I should call tool X because..."
4. You parse response, extract tool calls
5. Execute tools with the parameters
6. Pass results back to LLM for final answer

### 3. Write Tests (20 min)

In `tests/test_agent.py`:

- Test that tools initialize with correct names/descriptions
- Test that tools handle missing parameters gracefully
- Test that Agent initializes with correct tools
- Test cost calculation

```bash
pytest tests/test_agent.py -v
```

### 4. Deploy as API (15 min)

Create `app/main.py` with FastAPI endpoint:

```python
from fastapi import FastAPI
from app.agent import Agent

app = FastAPI()
agent = Agent("data/techcorp.db")

@app.post("/agent/query")
def query_agent(question: str, user_role: str = "engineer"):
    result = agent.query(question, user_role)
    return result

# TODO: add POST /agent/metrics endpoint
# TODO: add GET /health endpoint
```

Run locally:

```bash
python3 -m uvicorn app.main:app --reload
# Visit http://localhost:8000/docs for interactive API docs
```

---

## Data & Database

The TechCorp SQLite database (`data/techcorp.db`) contains:

**Tables:**

- `employees` - name, id, department, salary, role
- `policies` - policy_name, description, requirements
- `expense_policies` - role, approval_limit, per_diem_rules
- `documents` - policy documents as text for retrieval

**Your tools will query these tables.** Example:

```python
import sqlite3

def employee_lookup(name):
    conn = sqlite3.connect("data/techcorp.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE name LIKE ?", (f"%{name}%",))
    rows = cursor.fetchall()
    conn.close()
    return rows
```

---

## Cost Tracking

Gemini 2.5 Pro pricing (free tier included):

- Input: $0.075 per 1M tokens
- Output: $0.3 per 1M tokens

The Agent class automatically calculates:

```python
def _estimate_query_cost(input_tokens, output_tokens):
    input_cost = (input_tokens / 1_000_000) * 0.075
    output_cost = (output_tokens / 1_000_000) * 0.3
    return input_cost + output_cost

# After each query:
metrics = agent.get_metrics()
print(f"Total queries: {metrics['total_queries']}")
print(f"Total cost: ${metrics['total_cost']:.4f}")
print(f"Avg cost per query: ${metrics['avg_cost_per_query']:.4f}")
```

---

## Testing

```bash
# Unit tests
pytest tests/test_agent.py -v

# Manual testing
python3 -c "
from app.agent import Agent
agent = Agent('data/techcorp.db', api_key='YOUR_KEY')
result = agent.query('What is the travel policy?')
print(result['answer'])
print(f\"Cost: \${result['cost']:.4f}\")
"
```

---

## Deliverables

1. **`app/agent.py`** — Agent class with 3+ tools, tool execution loop, cost tracking
2. **`app/main.py`** — FastAPI endpoints (`/agent/query`, `/agent/metrics`, `/health`)
3. **`tests/test_agent.py`** — Unit tests for tools and agent (all passing)
4. **Screenshot** — 10 test queries showing working agent + total cost

## Grading

| Criterion | Weight |
|-----------|--------|
| Tools implemented (3+ with execute()) | 30% |
| Agent reasoning loop (LLM calls tools correctly) | 30% |
| Cost tracking (accurate token/cost calculation) | 20% |
| API functional (endpoints working) | 15% |
| Tests passing (tools + agent) | 5% |

---

## Common Issues

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Next Week

Week 6 will add access control and rate limiting. Build a solid agent foundation this week!
