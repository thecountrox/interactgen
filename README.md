# Browser Automation Agent

A sophisticated browser automation agent with a 3-layer architecture: **Reading → Judge → Actions**.

## Architecture

### 1. **Reading Layer** (BeautifulSoup)
- Scrapes and parses HTML content
- Extracts page structure and elements

### 2. **Judge Layer** (LLMs + RAG)
- Uses Google Gemini LLMs with Retrieval-Augmented Generation
- Stores user context and learned patterns in Supabase (pgvector)
- Makes intelligent decisions about UI modifications and actions

### 3. **Actions Layer** (Playwright)
- Executes browser automation
- Performs actions based on Judge layer decisions

### 4. **WebSocket Layer** (Helpful Chatbot)
- Real-time communication with browser extension
- Context-aware tips and assistance

## Tech Stack

- **Backend**: Python FastAPI
- **Database**: Supabase (PostgreSQL + pgvector)
- **LLM**: Google Gemini API
- **Automation**: Playwright
- **Browser Extension**: Chrome Manifest V3

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 2. Configure Supabase

Run the SQL setup script in your Supabase SQL Editor:

```bash
# The script is in supabase_setup.sql
```

This will create:
- `profiles` table for user data
- `memories` table for RAG with vector embeddings
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

### 4. Run the Server

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### REST Endpoints

#### `GET /`
Health check and service info

#### `GET /health`
Detailed health status

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

## TODO / Next Steps

- [ ] Implement actual embedding generation in `log_interaction_for_memory()`
- [ ] Complete Judge layer with Gemini API integration
- [ ] Add vector similarity search in `judge_page_context()`
- [ ] Build Chrome extension (Manifest V3)
- [ ] Implement Playwright actions executor
- [ ] Add authentication and user management
- [ ] Implement rate limiting
- [ ] Add monitoring and analytics
