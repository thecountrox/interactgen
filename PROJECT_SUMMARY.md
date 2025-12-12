# InteractGen - Complete Project Summary

## 🎯 What We Built

A **3-layer browser automation agent** with AI-powered personalization and proactive assistance.

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Browser Extension                       │
│            (Chrome Manifest V3 - To Build)              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ├──► HTTP POST /analyze (page context)
                 │
                 └──► WebSocket /chat/{user_id} (real-time)
                 │
┌────────────────▼────────────────────────────────────────┐
│             FastAPI Backend (main.py)                    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Layer 1: Reading (BeautifulSoup)             │    │
│  │  - Extract HTML structure                       │    │
│  │  - Parse page elements                          │    │
│  └────────────┬───────────────────────────────────┘    │
│               │                                          │
│  ┌────────────▼───────────────────────────────────┐    │
│  │  Layer 2: Judge (judge_engine.py)             │    │
│  │  - RAG: Query vector memories                  │    │
│  │  - LLM: Analyze with Gemini                    │    │
│  │  - Decide: What to hide/highlight/suggest      │    │
│  └────────────┬───────────────────────────────────┘    │
│               │                                          │
│  ┌────────────▼───────────────────────────────────┐    │
│  │  Layer 3: Actions (Playwright - To Build)     │    │
│  │  - Execute browser automation                  │    │
│  │  - Apply UI modifications                       │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Tertiary: Proactive Chat (tertiary_chat.py)  │    │
│  │  - Detect knowledge gaps                       │    │
│  │  - Generate contextual nudges                   │    │
│  │  - Push via WebSocket                           │    │
│  └────────────────────────────────────────────────┘    │
└───────────────┬──────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────┐
│           Supabase (PostgreSQL + pgvector)               │
│                                                          │
│  ┌──────────────┐  ┌────────────────────────────────┐  │
│  │   profiles   │  │        memories (RAG)          │  │
│  │              │  │  - content                      │  │
│  │  - username  │  │  - embedding (vector(768))     │  │
│  │  - tech_lvl  │  │  - metadata                     │  │
│  │  - personality│  │  - created_at                  │  │
│  └──────────────┘  └────────────────────────────────┘  │
│                                                          │
│  🔍 search_memories(query_embedding, user_id)           │
│  💾 insert_memory(user_id, content, embedding)          │
└──────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
interactgen/
├── main.py                    # FastAPI backend (core hub)
├── judge_engine.py            # Layer 2: LLM + RAG decision making
├── tertiary_chat.py           # Layer 4: Proactive tutor chatbot
├── gemini_api.py              # Gemini API integration
├── supabase_setup.sql         # Database schema with pgvector
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (filled)
├── .env.example              # Template for env vars
├── setup.fish                # Setup script (uv-based)
├── test_gemini.py            # Test Gemini API connection
├── test_judge.py             # Test Judge Engine
├── test_tertiary.py          # Test Tertiary Chat
├── README.md                 # Main project documentation
├── GEMINI_GUIDE.md           # Gemini API migration guide
├── TERTIARY_CHAT_GUIDE.md    # Proactive chat documentation
└── MIGRATION_SUMMARY.md      # OpenAI → Gemini migration notes
```

## ✅ Completed Features

### 1. **Memory Layer** (Supabase SQL) ✓
- [x] Enable pgvector extension
- [x] Create `profiles` table (username, technical_level, personality_type)
- [x] Create `memories` table with 768-dimensional vectors (Gemini embeddings)
- [x] Implement `search_memories()` function (cosine similarity)
- [x] Helper functions: `insert_memory()`, `get_user_context()`
- [x] Row Level Security policies (commented, ready for auth)

### 2. **Backend Skeleton** (FastAPI) ✓
- [x] Initialize FastAPI with lifespan management
- [x] Setup Supabase client from environment variables
- [x] Create `PageContext` Pydantic model (url, html_content, user_id, metadata)
- [x] POST `/analyze` endpoint with Judge function integration
- [x] WebSocket `/chat/{client_id}` with `ConnectionManager` class
- [x] Background task for memory embedding logging
- [x] CORS middleware configuration
- [x] Health check endpoints

### 3. **Judge Logic** (The Brains) ✓
- [x] Import and configure Gemini API
- [x] `evaluate_page(html, user_id)` async function
- [x] **Step 1 (RAG)**: Query top 3 relevant memories via vector similarity
- [x] **Step 2 (Prompting)**: Construct personalized prompts for Gemini
- [x] **Step 3 (Output)**: Return JSON with:
  - `summary`: 1-sentence page description
  - `hidden_selectors`: CSS selectors to hide (clutter)
  - `highlight_selectors`: CSS selectors to highlight
  - `suggested_action`: Next logical step
- [x] Fallback responses when LLM fails
- [x] CSS selector validation and sanitization
- [x] `store_interaction_memory()` for building RAG knowledge base

### 4. **Tertiary Chat** (Contextual Tutor) ✓
- [x] `generate_proactive_nudge(html_summary, user_profile)` function
- [x] Detect knowledge gaps (page complexity vs. user level)
- [x] Use Gemini for fast, context-aware nudge generation
- [x] Handle scenarios:
  - Beginner on advanced content ("simplify")
  - Slight challenge ("encourage")
  - Expert on basic content ("suggest_advanced")
  - Tutorial skipping for experts ("skip_basics")
  - Form assistance for beginners ("form_help")
- [x] Push nudges via WebSocket to active connections
- [x] Handle direct chat queries with context
- [x] Fallback templates when LLM unavailable

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI + Uvicorn | Async API server |
| **Database** | Supabase (PostgreSQL) | User data & memories |
| **Vector DB** | pgvector | Similarity search for RAG |
| **LLM** | Google Gemini API | Analysis & chat generation |
| **Embeddings** | Gemini embedding-001 (768d) | Vector representations |
| **Web Scraping** | BeautifulSoup | HTML parsing (Reading Layer) |
| **Automation** | Playwright | Browser actions (Layer 3 - TBD) |
| **WebSockets** | FastAPI WebSocket | Real-time chat |
| **Package Manager** | uv | Fast Python dependency mgmt |

## 🚀 Quick Start

### 1. Setup
```bash
# Clone and setup
cd interactgen
./setup.fish  # Or manually: uv venv && uv pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
#   - SUPABASE_URL
#   - SUPABASE_KEY
#   - GEMINI_API_KEY
```

### 2. Database Setup
```sql
-- Run supabase_setup.sql in Supabase SQL Editor
-- This creates tables, indexes, and functions
```

### 3. Start Server
```bash
uv run main.py
# Server runs on http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 4. Test the System
```bash
# Test Gemini API
uv run test_gemini.py

# Test Judge Engine
uv run test_judge.py

# Test Tertiary Chat
uv run test_tertiary.py
```

## 📡 API Usage Examples

### Analyze a Page
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "html_content": "<html>...</html>",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "metadata": {"viewport": "desktop"}
  }'
```

### WebSocket Chat
```javascript
const ws = new WebSocket('ws://localhost:8000/chat/user-123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'proactive_nudge') {
    console.log('Nudge:', data.message);
  }
};

ws.send(JSON.stringify({
  type: 'query',
  message: 'How do I use this form?'
}));
```

## 🎯 How It Works

### Complete Flow

1. **User visits a webpage** (via Chrome extension)
2. **Extension captures** HTML and sends POST to `/analyze`
3. **Reading Layer** (BeautifulSoup) extracts page structure
4. **Judge Layer** (judge_engine.py):
   - Queries Supabase for similar past interactions (RAG)
   - Sends context to Gemini LLM
   - Returns decisions: what to hide, highlight, suggest
5. **Tertiary Chat Layer** (tertiary_chat.py):
   - Analyzes knowledge gap (user level vs. page complexity)
   - Generates proactive nudge if needed
   - Pushes via WebSocket to user
6. **Actions Layer** (Playwright - to be built):
   - Executes browser automation based on Judge decisions
7. **Memory Storage** (background):
   - Generates embedding for interaction
   - Stores in Supabase for future RAG queries

### RAG (Retrieval-Augmented Generation)

```python
# 1. Generate embedding for current page
embedding = await generate_embedding(page_summary)

# 2. Search for similar past interactions
similar_memories = supabase.rpc('search_memories', {
    'query_embedding': embedding,
    'match_user_id': user_id,
    'match_threshold': 0.7,
    'match_count': 3
}).execute()

# 3. Include memories in LLM prompt
prompt = f"""
User's past experience:
{format_memories(similar_memories)}

Current page:
{page_context}

What should we suggest?
"""

# 4. LLM generates personalized response
response = await call_gemini(prompt)
```

## 🔮 Next Steps

### Immediate (Priority 1)
- [ ] Build Chrome Extension (Manifest V3)
  - Content script to capture page HTML
  - Background service worker for API calls
  - UI for displaying nudges and suggestions
- [ ] Implement Playwright Actions Layer
  - Execute hiding/highlighting from Judge decisions
  - Form auto-fill capabilities
  - Screenshot and logging
- [ ] User authentication (Supabase Auth)
- [ ] Create test user profiles in database

### Short-term (Priority 2)
- [ ] Rate limiting and quota management
- [ ] Nudge dismissal tracking (don't repeat)
- [ ] Learning from user feedback
- [ ] Analytics dashboard
- [ ] Multi-language support

### Long-term (Priority 3)
- [ ] Voice-based interaction
- [ ] Mobile app version
- [ ] Team collaboration features
- [ ] Custom automation scripts
- [ ] Marketplace for community automations

## 📊 Current Status

✅ **Fully Functional**:
- Memory layer with vector search
- FastAPI backend with WebSocket support
- Judge Engine with RAG + LLM
- Tertiary Chat with proactive nudges
- Comprehensive test suite

⚠️ **Known Limitations**:
- Gemini API quota limits on free tier
- No browser extension yet (needs to be built)
- Actions layer (Playwright) not implemented
- No user authentication

🔧 **Works Without API**:
- All endpoints function
- Fallback responses when LLM unavailable
- Database operations work independently

## 💡 Key Innovations

1. **3-Layer Architecture**: Clean separation of concerns (Read → Decide → Act)
2. **RAG-Powered Personalization**: Uses past interactions for context-aware decisions
3. **Proactive Knowledge Gap Detection**: Tertiary layer anticipates user needs
4. **Fallback Resilience**: Works even when AI APIs fail
5. **Real-time Communication**: WebSocket for instant nudges

## 🐛 Troubleshooting

### Server won't start?
```bash
# Check dependencies
uv pip list

# Verify .env file
cat .env | grep -v "^#"

# Check Supabase connection
python -c "from supabase import create_client; print('OK')"
```

### No nudges appearing?
1. Check WebSocket connection: `GET /connections`
2. Verify user has `technical_level` in profile
3. Check server logs for complexity detection
4. Test with `uv run test_tertiary.py`

### Gemini API errors?
- Free tier has strict rate limits
- Check quota at https://ai.google.dev/usage
- Fallback templates used automatically
- Consider upgrading to paid tier

## 📚 Documentation

- **Main README**: `README.md` - Project overview
- **Gemini Guide**: `GEMINI_GUIDE.md` - API usage
- **Tertiary Chat**: `TERTIARY_CHAT_GUIDE.md` - Proactive nudges
- **API Docs**: http://localhost:8000/docs (when running)
- **Database Schema**: `supabase_setup.sql` - Comments explain each table

## 🤝 Contributing

This is your personal project! Future enhancements could include:
- More sophisticated RAG strategies
- Multi-modal analysis (images, videos)
- Plugin system for custom behaviors
- Community-driven automation patterns

## 📄 License

[Your chosen license]

---

**Built with ❤️ using FastAPI, Supabase, and Google Gemini**

*Last Updated: December 12, 2025*
