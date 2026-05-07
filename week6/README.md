# Week 6 — Access Control & Monitoring

## Overview

This week you'll add guardrails to the Week 5 agent:
- **Access Control** — Enforce role-based access to documents and sensitive fields
- **Rate Limiting** — Limit queries per minute per user
- **Cost Enforcement** — Prevent users from exceeding their budget
- **Monitoring** — Track health metrics and detect anomalies

**Key concept:** Guardrails prevent misuse and unauthorized access. They should block requests *before* they reach the LLM, not after.

---

## Setup (10 minutes)

### 1. Install Dependencies

```bash
cd week6
pip install -r requirements.txt
```

### 2. Create Access Control Policy

You need `data/access_control.json` defining which roles can access which data:

```json
{
  "roles": {
    "engineer": {
      "permissions": {"documents": ["api_docs", "deployment_guides"], "fields": ["name", "email"]}
    },
    "manager": {
      "permissions": {"documents": ["all"], "fields": ["name", "email", "department"]}
    },
    "hr": {
      "permissions": {"documents": ["all"], "fields": ["all"]}
    }
  },
  "sensitive_fields": {
    "salary": {"visibility": ["manager", "hr"], "redact": true},
    "ssn": {"visibility": ["hr"], "redact": true},
    "medical_info": {"visibility": ["hr"], "redact": true}
  }
}
```

---

## Your Tasks

### 1. Implement AccessController (30 min)

In `app/access_control.py`, implement the `AccessController` class:

```python
class AccessController:
    """Enforce role-based access control."""

    def __init__(self, access_policy_path: str):
        # TODO: Load JSON policy
        # TODO: Store in memory
        pass

    def can_view_document(self, role: str, document: Dict) -> bool:
        """Check if role can view this document."""
        # TODO: Check document sensitivity vs role permissions
        pass

    def can_view_field(self, role: str, field_name: str) -> bool:
        """Check if role can view this field."""
        # TODO: Check field in sensitive_fields
        pass

    def redact_response(self, role: str, response: str) -> str:
        """Redact sensitive fields from response."""
        # TODO: Find sensitive fields in response
        # TODO: Replace with [REDACTED]
        pass

    def log_access(self, role: str, resource: str, allowed: bool):
        """Log access attempt for audit."""
        # TODO: Append to audit_log with timestamp
        pass

    def filter_documents(self, role: str, documents: List) -> List:
        """Filter documents based on role."""
        # TODO: Return only documents role can view
        pass
```

### 2. Implement RateLimiter (15 min)

In the same file, implement `RateLimiter`:

```python
class RateLimiter:
    """Rate limit queries per user per minute."""

    def __init__(self, max_queries_per_minute: int = 30):
        pass

    def is_allowed(self, user_id: str) -> bool:
        """Check if user can make another query."""
        # TODO: Track query times per user
        # TODO: Count queries in last 60 seconds
        # TODO: Return False if at limit
        pass

    def get_remaining_queries(self, user_id: str) -> int:
        """Get remaining queries for user."""
        # TODO: Return max - current queries in last minute
        pass
```

### 3. Implement CostEnforcer (15 min)

In the same file, implement `CostEnforcer`:

```python
class CostEnforcer:
    """Enforce budget limits per role."""

    def __init__(self, policy_path: str = None):
        # TODO: Load role budgets:
        # engineer: $100/month
        # manager: $500/month
        # hr: $200/month
        # finance: $500/month
        # executive: $1000/month
        pass

    def add_cost(self, user_id: str, role: str, cost: float):
        """Track spending for user."""
        # TODO: Add to user_spending dict
        pass

    def can_afford_query(self, user_id: str, estimated_cost: float) -> bool:
        """Check if user has budget remaining."""
        # TODO: Get user's budget
        # TODO: Get user's spending so far
        # TODO: Return True if estimated_cost <= remaining_budget
        pass

    def get_budget_remaining(self, user_id: str) -> float:
        """Get remaining budget for user."""
        # TODO: Calculate budget - spending
        pass
```

### 4. Write Tests (15 min)

In `tests/test_access_control.py`, write tests for:
- AccessController initialization loads policy
- can_view_document() returns correct values
- Field redaction removes sensitive data
- Audit logging works
- RateLimiter blocks after limit
- CostEnforcer blocks when budget exceeded

Run:
```bash
pytest tests/test_access_control.py -v
```

All tests should pass.

### 5. Integrate with Week 5 Agent (20 min)

Update your Week 5 `app/agent.py` to use access control:

```python
class Agent:
    def __init__(self, db_path: str, api_key: str = None):
        # ... existing code ...
        self.access_controller = AccessController("data/access_control.json")
        self.rate_limiter = RateLimiter(max_queries_per_minute=30)
        self.cost_enforcer = CostEnforcer()

    def query(self, user_query: str, user_id: str, user_role: str = "engineer"):
        # Check access
        if not self.rate_limiter.is_allowed(user_id):
            return {"error": "Rate limit exceeded"}

        estimated_cost = 0.01  # Estimate
        if not self.cost_enforcer.can_afford_query(user_id, estimated_cost):
            return {"error": "Budget exceeded"}

        # ... execute query ...
        
        # Track cost
        actual_cost = 0.005  # Actual
        self.cost_enforcer.add_cost(user_id, user_role, actual_cost)
        
        # Redact response
        answer = answer_from_llm
        answer = self.access_controller.redact_response(user_role, answer)
        
        return {"answer": answer, "cost": actual_cost}
```

---

## Testing

```bash
# Unit tests
pytest tests/test_access_control.py -v

# Manual testing
python3 << 'EOF'
from app.access_control import AccessController, RateLimiter, CostEnforcer

# Test access control
controller = AccessController("data/access_control.json")
assert controller.can_view_field("engineer", "name")
assert not controller.can_view_field("engineer", "salary")

# Test rate limiting
limiter = RateLimiter(max_queries_per_minute=3)
assert limiter.is_allowed("user1")
assert limiter.is_allowed("user1")
assert limiter.is_allowed("user1")
assert not limiter.is_allowed("user1")  # 4th query blocked

# Test cost enforcement
enforcer = CostEnforcer()
assert enforcer.can_afford_query("user1", 50.0)  # Within budget
enforcer.add_cost("user1", "engineer", 50.0)
assert enforcer.can_afford_query("user1", 51.0)  # False (total would be 101, limit is 100)
EOF
```

---

## Deliverables

1. **`app/access_control.py`** — AccessController, RateLimiter, CostEnforcer classes
2. **`tests/test_access_control.py`** — Unit tests (all passing)
3. **Updated `app/agent.py`** — Integrated with access control guardrails
4. **`data/access_control.json`** — Access policy configuration
5. **Screenshot** — Test queries with different roles (allowed/denied/redacted)

## Grading

| Criterion | Weight |
|-----------|--------|
| AccessController (role-based access working) | 30% |
| RateLimiter (tracks queries per minute) | 20% |
| CostEnforcer (tracks budgets, blocks when exceeded) | 20% |
| Integration (agent uses all guardrails) | 20% |
| Tests passing (all access control tests) | 10% |

---

## Common Issues

**Access control not working?** → See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Next Week

Week 7 will add:
- Cost optimization (caching, model selection, etc.)
- Feedback loops (learning from corrections)
- Advanced monitoring

Implement solid access control this week!
