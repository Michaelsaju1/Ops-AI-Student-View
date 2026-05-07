# Week 5 Troubleshooting Guide

## Setup Issues

### API Key Not Found
**Error:** `ValueError: GOOGLE_API_KEY environment variable not set`

**Solution:**
1. Get free API key at https://aistudio.google.com/app/apikey
2. Set environment variable:
   ```bash
   export GOOGLE_API_KEY="your-key-here"
   ```
3. Or pass directly to Agent:
   ```python
   agent = Agent("data/techcorp.db", api_key="your-key-here")
   ```

### API Key Invalid
**Error:** `400 INVALID_ARGUMENT: API key not valid`

**Solution:**
- Verify key from https://aistudio.google.com/app/apikey
- Key should start with `AIza...`
- Check for extra spaces or line breaks in .env file
- Try generating a new key

### ModuleNotFoundError: google.genai
**Error:** `ModuleNotFoundError: No module named 'google.genai'`

**Solution:**
```bash
pip install --upgrade google-genai
```

## Runtime Issues

### Model Not Available
**Error:** `404 Requested entity was not found`

**Solution:**
- Verify you're using `gemini-2.5-pro` (or check available models)
- Try `gemini-1.5-flash` as fallback (faster, cheaper)
- Check https://ai.google.dev/ for current model availability

### Rate Limit Exceeded
**Error:** `429 Resource exhausted`

**Solution:**
- Free tier has request limits
- Wait 60 seconds before retrying
- Implement exponential backoff in your code:
  ```python
  import time
  for attempt in range(3):
      try:
          result = agent.query(question)
          return result
      except RateLimitError:
          if attempt < 2:
              time.sleep(2 ** attempt)
  ```

### Firestore Connection Error
**Error:** `google.cloud.exceptions.PermissionDenied`

**Solution:**
- Firestore is optional (for full RAG)
- For basic agent, skip Firestore; implement simple in-memory document retrieval
- To use Firestore: `gcloud auth application-default login`

## Testing Issues

### Tests Fail: Database Not Found
**Error:** `FileNotFoundError: data/techcorp.db`

**Solution:**
```bash
# Verify file exists
ls -lh week5/data/techcorp.db

# If missing, recreate it:
python3 -c "
import sqlite3
conn = sqlite3.connect('week5/data/techcorp.db')
conn.execute('CREATE TABLE IF NOT EXISTS employees (id TEXT, name TEXT)')
conn.commit()
"
```

### Tests Fail: "test_agent_initialization" 
**Error:** Tests expect agent to initialize without API key

**Solution:**
- Tests should use dummy key: `Agent("data/techcorp.db", api_key="test-key")`
- Tests should mock API calls for unit tests
- See `week5-implemented/tests/test_agent.py` for examples

## Deployment Issues

### Container Build Fails
**Error:** `pip: command not found` in Docker

**Solution:**
- Ensure Dockerfile uses `pip3` or `/usr/local/bin/pip`
- Verify requirements.txt is copied before `pip install`

### Service Endpoint Not Responding
**Error:** Connection refused on localhost:8000

**Solution:**
1. Check if service is running:
   ```bash
   curl http://localhost:8000/docs  # FastAPI swagger UI
   ```
2. If not running:
   ```bash
   python3 -m uvicorn app.main:app --reload
   ```
3. Check logs:
   ```bash
   docker logs <container-id>
   kubectl logs deployment/agent -n default
   ```

## Common Questions

**Q: Do I need Firestore for RAG?**
A: Not required. You can implement basic RAG with in-memory document indexing or simple keyword search first. Firestore is optional for production.

**Q: Can I use a different LLM?**
A: Yes! Google GenAI SDK supports multiple models. Check https://ai.google.dev/ for current options. Update your Agent class to use a different model_id.

**Q: How do I track costs?**
A: Agent automatically calculates tokens → cost. Call `agent.get_metrics()` after queries to see totals.

**Q: Is there a maximum query size?**
A: Gemini 2.5 Pro supports ~100K tokens. Most enterprise queries are <2K tokens, so you're safe.
