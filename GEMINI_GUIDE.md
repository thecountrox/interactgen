# Gemini API Integration Guide

## Overview

This project uses **Google Gemini API** instead of OpenAI for:
- **LLM analysis** (gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash-exp)
- **Embedding generation** (embedding-001, 768 dimensions)

## Getting Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key and add it to `.env`:
   ```bash
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

## Key Differences from OpenAI

| Feature | OpenAI | Gemini |
|---------|--------|--------|
| Embedding dimension | 1536 | **768** |
| Embedding model | text-embedding-ada-002 | embedding-001 |
| LLM models | gpt-4, gpt-3.5-turbo | gemini-1.5-flash, gemini-1.5-pro |
| API package | `openai` | `google-generativeai` |
| Cost | $0.0001 per 1K tokens (embedding) | **Free tier available** |

## Vector Dimension Update

⚠️ **Important**: The `memories` table uses `vector(768)` instead of `vector(1536)`.

If you already ran the old SQL script, you need to:

```sql
-- Drop the old table
DROP TABLE IF EXISTS memories CASCADE;

-- Then re-run the updated supabase_setup.sql
```

## Available Models

### Embedding Models
- `models/embedding-001` - 768 dimensions (default)

### LLM Models
- `gemini-1.5-flash` - Fast, cost-effective (default in code)
- `gemini-1.5-pro` - More capable, better reasoning
- `gemini-2.0-flash-exp` - Experimental, latest features

## Usage Examples

### Generate Embeddings
```python
from gemini_api import generate_embedding

# For documents/content
embedding = await generate_embedding("User visited example.com")

# For search queries
from gemini_api import generate_query_embedding
query_emb = await generate_query_embedding("find similar pages")
```

### Call Gemini LLM
```python
from gemini_api import call_gemini_with_context

result = await call_gemini_with_context(
    page_context={"url": "https://example.com", "html_content": "..."},
    user_context={"technical_level": "intermediate"},
    relevant_memories=[...]  # From RAG
)

print(result["suggestions"])
print(result["actions"])
```

### Chatbot Response
```python
from gemini_api import generate_chatbot_response

response = await generate_chatbot_response(
    user_message="How do I fill this form?",
    user_context={"technical_level": "beginner"},
    conversation_history=[...]
)
```

## Pricing (as of Dec 2024)

### Free Tier
- 15 requests per minute
- 1,500 requests per day
- 1 million tokens per day

### Paid Tier (Pay-as-you-go)
- Gemini 1.5 Flash: $0.075 / 1M input tokens
- Gemini 1.5 Pro: $1.25 / 1M input tokens
- Embeddings: **Free**

Much more cost-effective than OpenAI! 💰

## Migration Checklist

If migrating from OpenAI:

- [x] Update `requirements.txt` (replace `openai` with `google-generativeai`)
- [x] Update `.env.example` (GEMINI_API_KEY instead of OPENAI_API_KEY)
- [x] Update `supabase_setup.sql` (vector(768) instead of vector(1536))
- [x] Create `gemini_api.py` helper module
- [x] Update `main.py` imports
- [x] Update documentation (README.md)
- [ ] Run `./setup.fish` to install new dependencies
- [ ] Update `.env` with your Gemini API key
- [ ] Re-run SQL script in Supabase (if needed)

## Testing Your Setup

```python
# Test in Python REPL or notebook
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Test embedding
result = genai.embed_content(
    model="models/embedding-001",
    content="Hello, world!",
    task_type="retrieval_document"
)
print(f"Embedding dimension: {len(result['embedding'])}")  # Should be 768

# Test LLM
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Say hello!")
print(response.text)
```

## Resources

- [Gemini API Documentation](https://ai.google.dev/docs)
- [Python SDK Reference](https://ai.google.dev/api/python/google/generativeai)
- [Pricing Details](https://ai.google.dev/pricing)
- [Google AI Studio](https://makersuite.google.com/)

## Troubleshooting

### "GEMINI_API_KEY not set"
Make sure your `.env` file has:
```bash
GEMINI_API_KEY=your-actual-key-here
```

### Import Error: "google.generativeai could not be resolved"
Run: `uv pip install google-generativeai`

### Vector Dimension Mismatch
Your SQL table expects 768 dimensions. If you see errors, check:
1. SQL table definition: `embedding vector(768)`
2. Using correct model: `models/embedding-001`

### Rate Limiting
Free tier has limits. If you hit them:
1. Add retry logic with exponential backoff
2. Consider paid tier
3. Cache embeddings when possible
