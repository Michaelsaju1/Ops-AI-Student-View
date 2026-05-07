# Week 6 Troubleshooting Guide — Access Control & Monitoring

## Common Issues

### AccessController Initialization Fails
**Error:** `FileNotFoundError: data/access_control.json not found`

**Solution:**
- Create `data/access_control.json` with proper structure:
  ```json
  {
    "roles": {
      "engineer": {"permissions": {...}},
      "manager": {"permissions": {...}}
    },
    "sensitive_fields": {
      "salary": {"visibility": ["manager", "hr"], "redact": true},
      "ssn": {"visibility": ["hr"], "redact": true}
    }
  }
  ```
- See `week6-implemented/data/access_control.json` for example

### Rate Limiter Not Working
**Error:** Rate limit tests pass locally but not in production

**Solution:**
- Rate limiter tracks per-minute queries in memory
- In distributed systems, this doesn't work across multiple pods
- For production: use Redis-backed rate limiting
- For now (learning): use in-memory is fine for single-instance deployment

### Cost Enforcer Always Returns True
**Error:** `can_afford_query()` always returns True even when budget exceeded

**Solution:**
- Verify `add_cost()` is being called for every query
- Check that user_role matches a key in `role_budgets`
- Example:
  ```python
  enforcer = CostEnforcer()
  enforcer.add_cost("user1", "engineer", 50.0)
  enforcer.add_cost("user1", "engineer", 60.0)
  # Now total=110, engineer budget=100, so can_afford_query("user1", 10) = False
  ```

### Field Redaction Doesn't Work
**Error:** Sensitive fields not being redacted from responses

**Solution:**
- Verify field is listed in `sensitive_fields` in access_control.json
- Verify regex pattern is correct
- Test redaction:
  ```python
  controller = AccessController('data/access_control.json')
  response = 'Employee salary: $100,000'
  redacted = controller.redact_response("engineer", response)
  assert "salary" in redacted.lower() and "$100,000" not in redacted
  ```

### Audit Log Growing Too Large
**Error:** `audit_log_size_mb()` returns huge number

**Solution:**
- Audit logs can grow quickly with many queries
- Implement log rotation:
  ```python
  if controller.audit_log_size_mb() > 10:  # 10 MB threshold
      # Archive old logs
      archive_logs(controller.audit_log)
      controller.audit_log = []
  ```
- Or trim to recent entries:
  ```python
  if len(controller.audit_log) > 10000:
      controller.audit_log = controller.audit_log[-5000:]  # Keep last 5000
  ```

## Testing Issues

### Test Fails: "missing data/access_control.json"
**Solution:**
```bash
# Create minimal config for testing
mkdir -p week6/data
python3 << 'EOF'
import json
config = {
    "roles": {
        "engineer": {"permissions": {}},
        "manager": {"permissions": {}}
    },
    "sensitive_fields": {
        "salary": {"visibility": ["manager"], "redact": true}
    }
}
with open('week6/data/access_control.json', 'w') as f:
    json.dump(config, f)
EOF
```

### MonitoringMetrics Tests Fail
**Solution:**
- Verify PII detector regex patterns work:
  ```python
  from app.monitoring import PIIDetector
  detector = PIIDetector()
  
  # Should detect SSN pattern XXX-XX-XXXX
  assert detector.has_ssn("123-45-6789")
  
  # Should detect email
  assert detector.has_email("user@example.com")
  ```

## Performance Issues

### Rate Limiter Too Strict
**Issue:** `is_allowed()` returns False even with low traffic

**Solution:**
- Rate limiter measures per-minute
- If user hits limit at :59 seconds, they can't query again until 1 minute passes
- Increase `max_queries_per_minute` or implement sliding window

### Audit Logging Slows Down Queries
**Issue:** Every query call to `log_access()` is slow

**Solution:**
- For high-traffic systems, implement async logging:
  ```python
  import threading
  
  def log_access_async(self, ...):
      thread = threading.Thread(target=self.log_access, args=(role, resource, allowed, field))
      thread.daemon = True
      thread.start()
  ```

## Deployment Issues

### Access Control JSON Not Loaded in Container
**Error:** Logs show "Failed to load access policy"

**Solution:**
- Verify JSON is copied into Docker image
- In Dockerfile:
  ```dockerfile
  COPY data/access_control.json /app/data/access_control.json
  ```
- Check path is correct in app (should be relative to working directory)

## FAQ

**Q: Why track audit logs if they get huge?**
A: For security/compliance. In production, ship logs to Cloud Logging or Datadog for long-term storage.

**Q: Should cost limits be per-minute or per-day?**
A: Start with per-day to avoid blocking legitimate users. Adjust based on usage patterns.

**Q: How do I know if someone is trying to access data they shouldn't?**
A: Check audit logs for pattern: same user_role, resource, allowed=False repeated many times = suspicious.
