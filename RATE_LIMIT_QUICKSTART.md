# ⚡ Rate Limiting Quick Reference

## 🚀 Quick Setup

```bash
# 1. Add to .env
echo "TRIAL_GEMINI_TOKEN=true" >> .env

# 2. Restart server
uv run main.py
```

## 📊 Check Status

```bash
# Via API
curl http://localhost:8000/api/rate-limit-status

# In Python
from rate_limiter import get_usage_stats
print(get_usage_stats())
```

## ⚙️ Configuration

| Setting | Purpose |
|---------|---------|
| `TRIAL_GEMINI_TOKEN=true` | **FREE TIER** - Enforces rate limits |
| `TRIAL_GEMINI_TOKEN=false` | **PAID TIER** - No rate limiting |

## 📏 Free Tier Limits

- 🕐 **15 requests/minute**
- 📅 **1,500 requests/day**
- ⏱️ **4 seconds minimum delay**

## 🧪 Test It

```bash
# Run test suite
uv run test_rate_limiter.py
```

## 🔍 What You'll See

```
⏳ Rate limit: waiting 4.0s...        # Normal operation
⏳ Rate limit: waiting 2.3 minutes... # Per-minute limit hit
⏳ Rate limit: waiting 1.2 hours...   # Daily limit hit
```

## 🆘 Troubleshooting

### Still getting 429 errors?

1. Check `.env` has `TRIAL_GEMINI_TOKEN=true`
2. Restart server after changing `.env`
3. Verify: `curl http://localhost:8000/api/rate-limit-status`

### Requests too slow?

- **On free tier?** This is normal (4s per request)
- **On paid tier?** Set `TRIAL_GEMINI_TOKEN=false`

### Quota exhausted?

- Wait 24 hours for reset
- Or get new API key: https://ai.google.dev/

## 📚 Full Docs

- **Complete Guide:** `RATE_LIMITING_GUIDE.md`
- **Implementation:** `RATE_LIMITING_SUMMARY.md`
- **Test Code:** `test_rate_limiter.py`

---

**Pro Tip:** Monitor `/api/rate-limit-status` to see when you're approaching limits!
