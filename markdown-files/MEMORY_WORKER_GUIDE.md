# Memory Worker - Background Learning Guide

## Overview

The **Memory Worker** is responsible for converting user interactions into searchable memories that power the RAG (Retrieval-Augmented Generation) system.

### What It Does

1. **Processes interactions** - Takes user activity and page context
2. **Generates embeddings** - Uses Gemini API to create 768-dimensional vectors
3. **Stores in Supabase** - Saves to the `memories` table with metadata
4. **Enables RAG** - Powers future similarity searches for personalization

## 🧠 Core Function

### `process_memory_background()`

This is the main function called as a FastAPI BackgroundTask.

```python
from memory_worker import process_memory_background

# In your endpoint
background_tasks.add_task(
    process_memory_background,
    user_id="user-uuid-here",
    interaction_summary="User filled out contact form on example.com",
    supabase=supabase,
    metadata={"url": "https://example.com/contact", "action": "form_submission"}
)
```

### Parameters

- **user_id** (str): UUID of the user
- **interaction_summary** (str): Human-readable description of what happened
- **supabase** (Client): Supabase client instance
- **metadata** (Dict, optional): Additional context (URL, action type, etc.)

### Returns

- `True` if memory stored successfully
- `False` if failed (logged automatically)

## 📊 How It Works

```
User Action
    ↓
process_memory_background()
    ↓
┌─────────────────────┐
│ 1. Generate         │
│    Embedding        │ ← Gemini API (768-dim vector)
│                     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 2. Prepare          │
│    Memory Data      │ ← user_id, content, embedding, metadata
│                     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 3. Insert into      │
│    Supabase         │ ← memories table
│                     │
└─────────────────────┘
           ↓
    Memory Stored! ✅
```

## 🔌 Integration with Main.py

Already integrated! The `/analyze` endpoint automatically:

1. Analyzes the page (Judge Layer)
2. **Queues background task** to store memory
3. Returns response immediately (non-blocking)
4. Memory gets processed in the background

### Current Implementation

```python
# In main.py, /analyze endpoint
background_tasks.add_task(
    log_interaction_for_memory,  # This calls memory_worker internally
    str(context.user_id),
    context.url,
    context.html_content,
    context.metadata
)
```

## 📡 New API Endpoints

### 1. GET /memories/{user_id}

Get recent memories and statistics for a user.

```bash
curl http://localhost:8000/memories/user-123?limit=10
```

**Response:**
```json
{
  "user_id": "user-123",
  "stats": {
    "total_memories": 15,
    "oldest_memory": "2025-12-01T10:00:00Z",
    "newest_memory": "2025-12-12T15:30:00Z",
    "actions": {
      "visited page": 10,
      "form_submission": 3,
      "login": 2
    }
  },
  "recent_memories": [
    {
      "id": "mem-uuid",
      "content": "User visited https://example.com/login",
      "created_at": "2025-12-12T15:30:00Z",
      "metadata": {"url": "...", "action": "login"}
    }
  ]
}
```

### 2. POST /memories/search

Search memories using semantic similarity.

```bash
curl -X POST http://localhost:8000/memories/search \
  -d "user_id=user-123" \
  -d "query=login forms" \
  -d "top_k=5"
```

**Response:**
```json
{
  "query": "login forms",
  "user_id": "user-123",
  "count": 3,
  "results": [
    {
      "content": "User successfully logged in",
      "similarity": 0.89,
      "created_at": "2025-12-12T10:00:00Z",
      "metadata": {...}
    }
  ]
}
```

### 3. POST /memories/create-test

Create test memories for development.

```bash
curl -X POST http://localhost:8000/memories/create-test \
  -d "user_id=user-123" \
  -d "scenario=login"
```

**Scenarios:** `login`, `form`, `search`, `purchase`

## 🎯 Helper Functions

### `process_interaction_memory()`

Higher-level function for common interaction patterns.

```python
from memory_worker import process_interaction_memory

await process_interaction_memory(
    user_id="user-123",
    url="https://example.com/checkout",
    action="completed purchase",
    supabase=supabase,
    page_title="Checkout Page",
    metadata={"items": 3, "total": 99.99}
)
```

### `search_user_memories()`

Search a user's memories programmatically.

```python
from memory_worker import search_user_memories

memories = await search_user_memories(
    user_id="user-123",
    query="forms and registration",
    supabase=supabase,
    top_k=5,
    threshold=0.7
)

for memory in memories:
    print(f"{memory['similarity']:.2f}: {memory['content']}")
```

### `get_user_memory_stats()`

Get statistics about a user's memories.

```python
from memory_worker import get_user_memory_stats

stats = await get_user_memory_stats("user-123", supabase)
print(f"Total memories: {stats['total_memories']}")
print(f"Actions: {stats['actions']}")
```

## 🧪 Testing

### Run the test suite:

```bash
uv run test_memory.py
```

### What it tests:
1. **Memory creation** - Creates test memories via API
2. **Memory retrieval** - Fetches and displays user memories
3. **Semantic search** - Searches memories by meaning
4. **Integration** - Tests /analyze endpoint with memory storage

## 🔄 Batch Processing

Process multiple memories at once:

```python
from memory_worker import process_multiple_memories

memories = [
    {
        "user_id": "user-1",
        "content": "User searched for Python tutorials",
        "metadata": {"query": "python"}
    },
    {
        "user_id": "user-2",
        "content": "User completed signup",
        "metadata": {"form": "registration"}
    }
]

result = await process_multiple_memories(memories, supabase)
print(f"Success: {result['success_count']}, Failed: {result['failed_count']}")
```

## 🧹 Maintenance Functions

### Cleanup Old Memories

```python
from memory_worker import cleanup_old_memories

deleted = await cleanup_old_memories(
    user_id="user-123",
    supabase=supabase,
    days_to_keep=90  # Keep only last 90 days
)
print(f"Deleted {deleted} old memories")
```

### Deduplicate Memories

```python
from memory_worker import deduplicate_memories

removed = await deduplicate_memories(
    user_id="user-123",
    supabase=supabase,
    similarity_threshold=0.95
)
print(f"Removed {removed} duplicates")
```

## 💡 Best Practices

### 1. **Write Descriptive Summaries**

Bad:
```python
interaction_summary = "User clicked button"
```

Good:
```python
interaction_summary = "User clicked 'Submit' button on contact form at example.com/contact"
```

### 2. **Include Rich Metadata**

```python
metadata = {
    "url": "https://example.com/form",
    "action": "form_submission",
    "form_fields": ["name", "email", "message"],
    "page_title": "Contact Us",
    "timestamp": datetime.utcnow().isoformat()
}
```

### 3. **Handle Failures Gracefully**

The system already does this! When Gemini API fails:
- Error is logged
- Function returns `False`
- System continues normally
- No crash or user impact

### 4. **Don't Store Sensitive Data**

Never store:
- Passwords
- Credit card numbers
- Personal identifying information
- Session tokens

Instead, store high-level actions:
```python
# ✅ Good
"User completed payment for premium subscription"

# ❌ Bad
"User entered credit card 1234-5678-9012-3456"
```

## 🎬 Complete Example

```python
from fastapi import BackgroundTasks
from memory_worker import process_memory_background

@app.post("/user-action")
async def handle_user_action(
    user_id: str,
    action: str,
    url: str,
    background_tasks: BackgroundTasks
):
    """
    Handle a user action and store it as a memory.
    """
    
    # Build descriptive summary
    summary = f"User {action} on {url}"
    
    # Add metadata
    metadata = {
        "url": url,
        "action": action,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Queue background task (non-blocking!)
    background_tasks.add_task(
        process_memory_background,
        user_id=user_id,
        interaction_summary=summary,
        supabase=supabase,
        metadata=metadata
    )
    
    # Return immediately
    return {"success": True, "message": "Action recorded"}
```

## 🔮 How RAG Uses These Memories

When the Judge Engine analyzes a new page:

1. **Current page** → Generate embedding
2. **Search memories** → Find similar past interactions
3. **Build context** → "User has done X, Y, Z before"
4. **LLM analysis** → Make personalized decisions based on history

```python
# In judge_engine.py
relevant_memories = await retrieve_relevant_memories(
    supabase=supabase,
    user_id=user_id,
    html_content=html,
    top_k=3
)

# These memories inform the LLM prompt
prompt = f"""
User's past experience:
{format_memories(relevant_memories)}

Current page: {page_context}

What should we suggest?
"""
```

## 📊 Memory Schema

Each memory in Supabase contains:

```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    content TEXT,                    -- The interaction summary
    embedding vector(768),           -- Gemini embedding
    metadata JSONB,                  -- Flexible additional data
    created_at TIMESTAMP
);
```

## ⚠️ Known Limitations

1. **Gemini API Quota**: Free tier has strict limits
   - **Solution**: Fallback to storing without embedding (manual workaround)
   
2. **Storage Costs**: Vectors take space
   - **Solution**: Implement cleanup for old memories
   
3. **Processing Time**: Embedding generation takes ~1-2 seconds
   - **Solution**: Background tasks keep API fast

## 🐛 Troubleshooting

### No memories being stored?

1. Check server logs for errors
2. Verify Gemini API key is set
3. Check API quota: https://ai.google.dev/usage
4. Test with: `curl -X POST http://localhost:8000/memories/create-test?user_id=test-123&scenario=login`

### Search returns no results?

1. Verify memories exist: `GET /memories/{user_id}`
2. Check similarity threshold (lower it)
3. Try different search queries
4. Ensure embeddings were generated (check logs)

### Background tasks not running?

1. Confirm FastAPI version supports BackgroundTasks
2. Check that `await` is used correctly
3. Look for errors in server logs
4. Test synchronously first (without background task)

## 📚 Related Documentation

- **Main README**: `README.md` - Project overview
- **Judge Engine**: `judge_engine.py` - How memories are retrieved
- **Database Schema**: `supabase_setup.sql` - Memory table structure
- **API Docs**: http://localhost:8000/docs - Interactive testing

---

**The Memory Worker makes your agent smarter over time! 🧠**
