# Rate Limiting for Gemini API

## Overview

This project includes built-in rate limiting to comply with Gemini API free tier quotas. When enabled, it automatically prevents hitting API limits that would cause errors.

## Configuration

### Enable/Disable Rate Limiting

Add to your `.env` file:

```bash
# Set to "true" for free tier (enables rate limiting)
TRIAL_GEMINI_TOKEN=true

# Set to "false" for paid tier (no rate limiting)
TRIAL_GEMINI_TOKEN=false
```

**Default:** If not set, rate limiting is **disabled** by default.

## Free Tier Limits

When `TRIAL_GEMINI_TOKEN=true`, the system enforces these limits:

| Limit Type | Value |
|------------|-------|
| **Requests per minute** | 15 RPM |
| **Requests per day** | 1,500 RPD |
| **Tokens per minute** | 32,000 TPM |
| **Minimum delay between requests** | 4 seconds |

Source: https://ai.google.dev/pricing

## How It Works

### Automatic Rate Limiting

All Gemini API calls are automatically rate-limited when enabled:

1. **Embedding Generation** (`generate_embedding()`)
2. **Query Embeddings** (`generate_query_embedding()`)
3. **LLM Calls** (`call_gemini_simple()`, `call_gemini_with_context()`)
4. **Chatbot Responses** (`generate_chatbot_response()`)

### Rate Limiting Algorithm

The system uses a **token bucket algorithm** with multiple tracking windows:

```
Request → Check Rate Limits → Wait if Needed → Process Request
                ↓
    ┌───────────────────────┐
    │ Per-Minute Tracking   │ (Last 60 seconds)
    │ Per-Day Tracking      │ (Last 24 hours)
    │ Minimum Delay         │ (4 seconds between requests)
    └───────────────────────┘
```

### Wait Behavior

When rate limits are reached, the system will:

```python
⏳ Rate limit: waiting 3.5s...                    # Short wait
⏳ Rate limit: waiting 2.3 minutes...             # Moderate wait
⏳ Rate limit: waiting 1.2 hours (daily limit)... # Daily limit hit
```

**Important:** The request will complete eventually, just slower.

## Checking Rate Limit Status

### API Endpoint

```bash
curl http://localhost:8000/api/rate-limit-status
```

**Response:**
```json
{
  "timestamp": "2025-12-12T10:30:00Z",
  "rate_limiting": {
    "trial_mode": true,
    "requests_last_minute": 8,
    "minute_limit": 15,
    "requests_last_day": 342,
    "day_limit": 1500,
    "minute_remaining": 7,
    "day_remaining": 1158
  }
}
```

### Programmatic Access

```python
from rate_limiter import get_usage_stats

stats = get_usage_stats()
print(f"Minute: {stats['requests_last_minute']}/{stats['minute_limit']}")
print(f"Day: {stats['requests_last_day']}/{stats['day_limit']}")
print(f"Remaining today: {stats['day_remaining']}")
```

## Usage Examples

### Example 1: Normal Operation

```python
# With TRIAL_GEMINI_TOKEN=true
from gemini_api import generate_embedding

# First request - immediate
embedding1 = await generate_embedding("Hello world")

# Second request - waits 4 seconds automatically
embedding2 = await generate_embedding("Another request")
```

### Example 2: Batch Processing

```python
# Process multiple items with automatic rate limiting
items = ["text1", "text2", "text3", ...]

for item in items:
    # Rate limiter ensures we don't exceed limits
    embedding = await generate_embedding(item)
    # Will automatically wait if needed
```

### Example 3: Monitoring Usage

```python
from rate_limiter import get_usage_stats

async def process_with_monitoring():
    stats = get_usage_stats()
    
    if stats['day_remaining'] < 100:
        print("⚠️ Warning: Less than 100 requests remaining today!")
    
    # Continue processing
    await generate_embedding("some text")
```

## Performance Impact

### With Rate Limiting (`TRIAL_GEMINI_TOKEN=true`)

- **Throughput:** ~15 requests/minute = 900 requests/hour
- **Latency:** +4 seconds minimum between requests
- **Daily max:** 1,500 requests/day

### Without Rate Limiting (`TRIAL_GEMINI_TOKEN=false`)

- **Throughput:** Limited only by API tier
- **Latency:** No artificial delays
- **Daily max:** Depends on your API plan

## Best Practices

### 1. **Enable for Free Tier**

If you're using Gemini's free tier, **always** set `TRIAL_GEMINI_TOKEN=true`:

```bash
TRIAL_GEMINI_TOKEN=true
```

This prevents hitting quota errors like:
```
ResourceExhausted: 429 Quota exceeded
```

### 2. **Batch Processing Strategy**

When processing many items, monitor your quota:

```python
from rate_limiter import get_usage_stats

items = [...]  # Your data

for i, item in enumerate(items):
    # Check quota every 10 items
    if i % 10 == 0:
        stats = get_usage_stats()
        remaining = stats['day_remaining']
        
        if remaining < len(items) - i:
            print(f"⚠️ Not enough quota! Need {len(items)-i}, have {remaining}")
            break
    
    await process_item(item)
```

### 3. **Background Tasks**

For FastAPI background tasks, rate limiting works transparently:

```python
@app.post("/process")
async def process_endpoint(background_tasks: BackgroundTasks):
    # Background task will respect rate limits
    background_tasks.add_task(
        process_memory_background,
        user_id="...",
        interaction_summary="...",
        supabase=supabase
    )
    
    # Returns immediately, processing happens in background
    return {"status": "queued"}
```

### 4. **Upgrade When Needed**

If you hit daily limits regularly:

1. Monitor usage: `GET /api/rate-limit-status`
2. Track patterns: When do you hit limits?
3. Consider upgrading to paid tier
4. Update `.env`: `TRIAL_GEMINI_TOKEN=false`

## Troubleshooting

### "429 Quota exceeded" Errors

**Problem:** Still getting quota errors with `TRIAL_GEMINI_TOKEN=true`

**Solution:**
1. Check `.env` file actually has the setting
2. Restart server after changing `.env`
3. Verify with: `curl http://localhost:8000/api/rate-limit-status`

### Requests Taking Too Long

**Problem:** API calls are very slow

**Possible Causes:**
1. Rate limiting is enabled (`TRIAL_GEMINI_TOKEN=true`)
2. You've exceeded per-minute limits (waiting for cooldown)
3. Daily limit reached (long waits)

**Solutions:**
```bash
# Check status
curl http://localhost:8000/api/rate-limit-status

# If not on free tier, disable rate limiting
TRIAL_GEMINI_TOKEN=false
```

### Rate Limiter Not Working

**Problem:** Rate limiting not preventing errors

**Debug Steps:**
```python
from rate_limiter import get_rate_limiter

limiter = get_rate_limiter()
print(f"Enabled: {limiter.enabled}")
print(f"Trial mode: {os.getenv('TRIAL_GEMINI_TOKEN')}")

# If enabled=False but should be True, check .env file
```

## Testing Rate Limiter

### Test Script

```bash
uv run python -m rate_limiter
```

This will simulate 5 requests and show rate limiting in action:

```
🚦 Rate Limiter initialized (Trial Mode: True)
   • 15 requests per minute
   • 1,500 requests per day
   • 4.0s minimum delay between requests

📊 Making 5 test requests...

🔵 Request 1
✅ Request 1 allowed
   Minute: 1/15
   Day: 1/1500

🔵 Request 2
⏳ Rate limit: waiting 4.0s...
✅ Request 2 allowed
   Minute: 2/15
   Day: 2/1500

...
```

## Architecture

### Rate Limiter Class

```python
class RateLimiter:
    def __init__(self):
        self.enabled = TRIAL_MODE  # From .env
        self.minute_requests = deque()  # Rolling window
        self.day_requests = deque()     # Rolling window
        self.last_request_time = None   # For min delay
    
    async def acquire(self):
        """Wait if needed, then record request"""
        wait_time = self._get_wait_time()
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self._record_request()
```

### Integration Points

All Gemini API calls go through rate limiting:

```python
# In gemini_api.py
async def generate_embedding(text: str) -> List[float]:
    await rate_limit()  # ← Rate limiting applied here
    result = genai.embed_content(...)
    return result['embedding']
```

## Production Considerations

### Scaling

If you need higher throughput:

1. **Upgrade to paid tier**: Remove rate limiting
   ```bash
   TRIAL_GEMINI_TOKEN=false
   ```

2. **Use multiple API keys**: Rotate keys to increase limits
   ```python
   # Not implemented yet, but possible
   api_keys = ["key1", "key2", "key3"]
   ```

3. **Cache embeddings**: Store results to avoid regeneration
   ```python
   # Check cache before generating
   cached = await get_from_cache(text)
   if cached:
       return cached
   ```

### Monitoring

Add monitoring for production:

```python
# Example: Log rate limit hits
stats = get_usage_stats()
if stats['minute_remaining'] < 3:
    logger.warning("⚠️ Approaching per-minute limit!")

if stats['day_remaining'] < 100:
    logger.warning("⚠️ Running low on daily quota!")
```

---

**Summary:**
- Set `TRIAL_GEMINI_TOKEN=true` for free tier
- Set `TRIAL_GEMINI_TOKEN=false` for paid tier
- Check `/api/rate-limit-status` for current usage
- Rate limiting is automatic and transparent
