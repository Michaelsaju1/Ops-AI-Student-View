# Week 7 — Cost Optimization & Continuous Learning

## Overview

This final week you'll optimize your agent's cost and implement a feedback loop for continuous improvement:
- **Cost Analysis** — Breakdown costs by component and identify expensive queries
- **Optimization Strategies** — Caching, model selection, retrieval optimization
- **Feedback Loop** — Collect user corrections and measure improvement

**Key concept:** Agents are never perfect. Collect feedback, measure what breaks, and continuously improve.

---

## Setup (10 minutes)

### 1. Install Dependencies

```bash
cd week7
pip install -r requirements.txt
```

### 2. Prepare Test Queries

Create `scripts/test_queries.json` with diverse questions:

```json
{
  "test_queries": [
    {"question": "What is the travel policy?", "role": "engineer", "category": "policy"},
    {"question": "Who can approve expenses over $5000?", "role": "manager", "category": "approval"},
    {"question": "What is the NYC per diem rate?", "role": "finance", "category": "lookup"},
    {"question": "What is the compensation policy?", "role": "hr", "category": "hr"}
  ]
}
```

---

## Your Tasks

### 1. Implement CostAnalyzer (20 min)
In `app/cost_optimization.py`, implement `CostAnalyzer`:

```python
class CostAnalyzer:
    """Analyze and track query costs."""

    def __init__(self):
        # TODO: Initialize empty query history
        pass

    def record_query(self, query: Dict):
        """Record a query and its cost breakdown."""
        # TODO: Store query with cost components
        pass

    def get_cost_breakdown(self) -> Dict:
        """Get breakdown of costs by component."""
        # TODO: Calculate totals for retrieval, LLM, tools, errors
        pass

    def identify_cost_spikes(self) -> List:
        """Identify unusually expensive queries."""
        # TODO: Find queries > mean + 2*stdev
        pass
```

### 2. Implement OptimizationStrategy (20 min)

In the same file, implement `OptimizationStrategy`:

```python
class OptimizationStrategy:
    """Optimize agent costs through caching, model selection, etc."""

    def __init__(self):
        # TODO: Initialize cache and strategy tracking
        pass

    def apply_caching(self, query: str, response: str) -> tuple:
        """Cache query responses.
        Return: (is_cached_hit, response)
        """
        # TODO: Store query→response, return cached if exists
        pass

    def optimize_retrieval_count(self, num_docs: int) -> int:
        """Reduce documents retrieved.
        Input 15 docs → output 3 docs
        """
        # TODO: Return reduced count
        pass

    def select_model_by_complexity(self, query: str) -> str:
        """Choose cheaper model for simple queries.
        Simple → gemini-1.5-flash (cheaper)
        Complex → gemini-2.5-pro
        """
        # TODO: Analyze query and return model name
        pass

    def enable_response_compression(self, response: str) -> str:
        """Compress long responses."""
        # TODO: Reduce response length
        pass

    def get_optimization_impact(self) -> Dict:
        """Estimate cost savings from optimizations."""
        # TODO: Return savings percentage and breakdown
        pass
```

### 3. Implement FeedbackLoop (15 min)

In the same file, implement `FeedbackLoop`:

```python
class FeedbackLoop:
    """Collect and validate user corrections."""

    def __init__(self):
        # TODO: Initialize corrections list
        pass

    def submit_correction(self, original_query: str, original_answer: str,
                         corrected_answer: str, user_role: str) -> Dict:
        """Submit a correction.
        TODO: Validate and store
        Return: {"accepted": True/False}
        """
        pass

    def validate_correction(self, index: int) -> bool:
        """Validate a correction is accurate.
        TODO: Check user authority, answer quality
        """
        pass

    def get_feedback_metrics(self) -> Dict:
        """Metrics on feedback quality."""
        # TODO: Return corrections count, validation rate, etc
        pass
```

### 4. Write Tests (20 min)

In `tests/test_cost_optimization.py`, test all three classes.

Run:
```bash
pytest tests/test_cost_optimization.py -v
```

### 5. Evaluate Your Agent (15 min)

Create `scripts/evaluate_agent.py` to test 10+ queries and show cost breakdown.

---

## Testing

```bash
pytest tests/test_cost_optimization.py -v
```

---

## Deliverables

1. **`app/cost_optimization.py`** — CostAnalyzer, OptimizationStrategy, FeedbackLoop
2. **`tests/test_cost_optimization.py`** — Unit tests (all passing)
3. **`scripts/evaluate_agent.py`** — Evaluation script for cost analysis
4. **`scripts/test_queries.json`** — 10+ diverse test queries
5. **Screenshot** — Cost breakdown, optimization impact, feedback loop examples

## Grading

| Criterion | Weight |
|-----------|--------|
| Cost analysis (breakdown by component working) | 25% |
| Spike detection (identifies expensive queries) | 20% |
| Optimization strategies (caching, model selection) | 25% |
| Feedback loop (collects corrections, measures impact) | 20% |
| Tests passing (cost optimization tests) | 10% |

---

## Common Issues

**Caching not working?** → See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Course Complete! 

You've built a complete agent system:
- **Week 5** - Agent with tools and LLM
- **Week 6** - Access control and guardrails  
- **Week 7** - Cost optimization and feedback loops

Congratulations on completing the Operationalizing AI course!
