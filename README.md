# Browser Automation Agent

A sophisticated browser automation agent with a 3-layer architecture: **Reading → Judge → Actions**.

## Team 13
### Prajol David ( RA2211003020539 )
### Akash K ( RA2211030020072 )

## Architecture

### 1. **Reading Layer** (BeautifulSoup)
- Scrapes and parses HTML content
- Extracts page structure and elements

### 2. **Judge Layer** (LLMs + RAG)
- Uses Google Gemini LLMs with Retrieval-Augmented Generation
- Stores user context and learned patterns in Supabase (pgvector)
- Makes intelligent decisions about UI modifications and actions

### 3. **Browser Extension** (Client-side Actions)
- Chrome extension executes DOM manipulations directly
- No separate browser instance needed
- Actions applied in real-time to user's current tab

### 4. **WebSocket Layer** (Helpful Chatbot)
- Real-time communication with browser extension
- Context-aware tips and assistance

## Tech Stack

- **Backend**: Python FastAPI
- **Database**: Supabase (PostgreSQL + pgvector)
- **LLM**: Google Gemini API **or** Local Models (Ollama)
- **Browser Extension**: Chrome Manifest V3 (client-side DOM manipulation)

## Key Features

- **RAG-Powered Analysis**: Learns from past interactions using vector embeddings
- **Proactive Tutoring**: Detects knowledge gaps and offers contextual help
- **Local LLM Support**: Run completely offline with Ollama (optional)
- **Background Learning**: Automatically stores interactions for future reference
- **Smart Rate Limiting**: Automatic API quota management for Gemini free tier
- **Real-time Communication**: WebSocket-based chat for instant assistance
- **Intelligent Page Analysis**: LLM-powered evaluation of web pages

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended - 10-100x faster)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Or using pip
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Supabase

Run the SQL setup script in your Supabase SQL Editor:

```bash
# The script is in supabase_setup.sql
```

This will create:
- `profiles` table for user data
- `memories` table for RAG with vector embeddings (768-dimensional)
- Helper functions for similarity search

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon/service key
- `GEMINI_API_KEY`: Your Google Gemini API key
- `TRIAL_GEMINI_TOKEN`: Set to `true` for free tier (enables rate limiting)

### 4. Run the Server

```bash
# Using uv (recommended)
uv run main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`

### 5. Rate Limiting (Free Tier)

If using Gemini's free tier, enable rate limiting to avoid quota errors:

```bash
# Add to .env
TRIAL_GEMINI_TOKEN=true
```

This enforces:
- 15 requests/minute
- 1,500 requests/day
- 4 second minimum delay

**Check status:** `curl http://localhost:8000/api/rate-limit-status`

**See:** `RATE_LIMIT_QUICKSTART.md` for details

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### User Management

#### `POST /user/onboard`
Create a new user profile

**Request Body:**
```json
{
  "username": "johndoe",
  "personality_type": "analytical",
  "technical_level": "intermediate"
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "personality_type": "analytical",
  "technical_level": "intermediate",
  "created_at": "2025-12-12T10:30:00Z",
  "updated_at": "2025-12-12T10:30:00Z"
}
```

#### `GET /user/{user_id}`
Retrieve user profile by ID

#### `PUT /user/{user_id}/preferences`
Update user preferences (supports partial updates)

**Request Body:**
```json
{
  "personality_type": "creative",
  "technical_level": "expert"
}
```

#### `DELETE /user/{user_id}`
Delete user account and all associated data

> **Full Documentation**: See [USER_ENDPOINTS_GUIDE.md](markdown-files/USER_ENDPOINTS_GUIDE.md) for complete API reference, examples, and integration guides.

### Page Analysis

#### `GET /`
Health check and service info

#### `GET /health`
Detailed health status

#### `GET /api/rate-limit-status`
Current API rate limiting statistics

#### `POST /analyze`
Analyze page context using the Judge layer

**Request Body:**
```json
{
  "url": "https://example.com",
  "html_content": "<html>...</html>",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "viewport": "desktop"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Page analyzed successfully",
  "analysis_id": "analysis_1234567890",
  "suggestions": ["...", "..."],
  "actions": [
    {
      "type": "highlight",
      "selector": "button.primary"
    }
  ]
}
```

#### `POST /broadcast`
Broadcast message to all connected WebSocket clients

### WebSocket Endpoint

#### `WS /chat/{client_id}`
WebSocket connection for real-time chatbot

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8000/chat/user123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

**Send Messages:**
```javascript
ws.send(JSON.stringify({
  type: 'query',
  message: 'How do I fill this form?'
}));
```


## Workflow

1. **Browser Extension** captures page context
2. **POST /analyze** sends HTML to backend
3. **Judge Layer** analyzes using Gemini LLM + past memories (RAG)
4. **Background Task** logs interaction for future learning
5. **Response** returns suggested actions
6. **Actions Layer** (Playwright) executes automation
7. **WebSocket** sends real-time tips to user

## Documentation

- **[Quick Start](QUICK_START.md)** - Get up and running fast
- **[Ollama Quick Start](OLLAMA_QUICKSTART.md)** - Run locally with Ollama
- **[Rate Limiting](RATE_LIMIT_QUICKSTART.md)** - Free tier quota management
- **[Local Models Guide](LOCAL_MODELS_GUIDE.md)** - Complete local setup guide
- **[Memory Worker Guide](MEMORY_WORKER_GUIDE.md)** - Background learning system
- **[Tertiary Chat Guide](TERTIARY_CHAT_GUIDE.md)** - Proactive tutoring
- **[Gemini API Guide](GEMINI_GUIDE.md)** - LLM integration details
- **[Project Summary](PROJECT_SUMMARY.md)** - Complete architecture overview

