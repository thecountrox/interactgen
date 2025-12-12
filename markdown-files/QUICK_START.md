# 🚀 Quick Start Guide - InteractGen

## ✅ Setup Complete!

Your browser automation agent is ready. Here's everything you need to know to get started.

## 📊 What You Have

✅ **Backend Server** - FastAPI with 3-layer architecture  
✅ **Memory Layer** - Supabase with pgvector for RAG  
✅ **Judge Engine** - AI-powered page analysis  
✅ **Tertiary Chat** - Proactive tutor with knowledge gap detection  
✅ **WebSocket Support** - Real-time communication  

## 🎯 Server is Running!

Your server should be running at: **http://localhost:8000**

### Quick Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
Open in browser: **http://localhost:8000/docs**

## 🧪 Test the System

### 1. Test Individual Components
```bash
# Test Gemini API (may hit quota limits)
uv run test_gemini.py

# Test Judge Engine with sample HTML
uv run test_judge.py

# Test Tertiary Chat proactive nudges
uv run test_tertiary.py
```

### 2. Test the API Directly
```bash
# Health check
curl http://localhost:8000/

# Analyze a page
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "html_content": "<html><body><h1>Test</h1></body></html>",
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

## 📝 Create Test Data

### 1. Create a test user in Supabase
```sql
-- Run in Supabase SQL Editor
INSERT INTO profiles (username, technical_level, personality_type)
VALUES ('test_user', 'intermediate', 'analytical');
```

### 2. Get the user ID
```sql
SELECT id, username FROM profiles WHERE username = 'test_user';
```

### 3. Use that ID in API calls
Replace the `user_id` in your API requests with the UUID from step 2.

## 🌐 WebSocket Testing

### JavaScript (Browser Console)
```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/chat/test-user-123');

// Listen for messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Send a query
ws.send(JSON.stringify({
  type: 'query',
  message: 'How do I use this page?',
  page_context: {
    url: window.location.href
  }
}));
```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Your current configuration
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
GEMINI_API_KEY=your-gemini-key
```

### Known Limitations
⚠️ **Gemini API Free Tier**: Very limited quota for embeddings  
✅ **Fallback System**: Works even when quota exceeded  
💡 **Solution**: Enable billing or wait for quota reset  

## 🎬 Complete Workflow Example

### 1. User visits a page (simulated)
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "url": "https://react.dev/learn/advanced-hooks",
  "html_content": "<html><head><title>Advanced React Hooks</title></head><body><h1>useMemo and useCallback</h1><p>Optimize your components...</p></body></html>",
  "user_id": "YOUR-USER-ID-HERE",
  "metadata": {
    "viewport": "desktop",
    "user_agent": "Mozilla/5.0"
  }
}
EOF
```

### 2. Server processes (automatic):
- ✅ Judge Engine analyzes page
- ✅ RAG queries past memories
- ✅ LLM generates suggestions
- ✅ Tertiary Chat detects knowledge gap
- ✅ Proactive nudge sent via WebSocket (if connected)
- ✅ Memory stored for future RAG

### 3. Response includes:
```json
{
  "success": true,
  "message": "Page analyzed successfully",
  "suggestions": [
    "Analyzing page: https://react.dev/learn/advanced-hooks",
    "💡 This React Hooks guide assumes knowledge..."
  ],
  "actions": [
    {"type": "hide", "selector": ".advanced-settings"},
    {"type": "highlight", "selector": "button[type='submit']"}
  ]
}
```

## 📚 Architecture

```
Browser Extension (To Build)
        ↓
   POST /analyze
        ↓
┌───────────────────┐
│  Reading Layer    │ ← BeautifulSoup parses HTML
└────────┬──────────┘
         ↓
┌───────────────────┐
│  Judge Layer      │ ← LLM + RAG decides what to do
│  (judge_engine)   │
└────────┬──────────┘
         ↓
┌───────────────────┐
│  Tertiary Chat    │ ← Detects gaps, sends nudges
│  (background)     │
└────────┬──────────┘
         ↓
    WebSocket → User sees tip!
```

## 🔧 Common Commands

```bash
# Start server
uv run main.py

# Run with specific port
uvicorn main:app --host 0.0.0.0 --port 8080

# Check active WebSocket connections
curl http://localhost:8000/connections

# View logs in real-time
# (Server already displays logs)

# Stop server
# Press CTRL+C in the terminal running main.py
```

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 $(lsof -t -i:8000)

# Restart
uv run main.py
```

### Gemini API quota exceeded
- ✅ System uses fallback responses automatically
- 💡 Wait 24 hours for quota reset
- 💳 Or enable billing on Google Cloud

### No proactive nudges
1. User must be connected via WebSocket first
2. Check: `curl http://localhost:8000/connections`
3. Knowledge gap must exist (beginner on advanced page, etc.)

### Database connection issues
```bash
# Test Supabase connection
python -c "from supabase import create_client; import os; from dotenv import load_dotenv; load_dotenv(); print(create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')))"
```

## 📖 Next Steps

### Immediate
1. **Create test users** in Supabase `profiles` table
2. **Test the API** with the examples above
3. **Open browser** to http://localhost:8000/docs to explore

### Short-term
1. **Build Chrome Extension** to capture pages and connect
2. **Implement Actions Layer** (Playwright) for automation
3. **Add authentication** (Supabase Auth)

### Documentation
- **Full docs**: `PROJECT_SUMMARY.md`
- **Tertiary chat**: `TERTIARY_CHAT_GUIDE.md`
- **Gemini API**: `GEMINI_GUIDE.md`
- **Database schema**: `supabase_setup.sql`

## 💡 Pro Tips

1. **Use fallback responses**: System works even without AI APIs
2. **Monitor logs**: Server shows detailed information about each request
3. **Test incrementally**: Start with health checks, then simple analyze calls
4. **Check quotas**: https://ai.google.dev/usage for Gemini limits
5. **WebSocket first**: Connect via WS before calling /analyze to receive nudges

## 🎉 You're All Set!

Your browser automation agent is ready. The server is running, all components are integrated, and the fallback systems ensure it works even with API limitations.

**Start testing and building your Chrome extension!** 🚀

---

Questions? Check:
- API docs: http://localhost:8000/docs
- Server logs: Terminal running `main.py`
- Tests: Run any `test_*.py` file

