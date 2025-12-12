# Local Models Guide for RTX 3060 6GB

## 🎯 Recommended Models

For your RTX 3060 with 6GB VRAM, these models will work efficiently with Ollama:

### 1. **Text Generation (LLM) - Replace Gemini**

#### Primary Choice: **Llama 3.2 3B Instruct**
```bash
ollama pull llama3.2:3b-instruct-q4_K_M
```
- **Size:** ~2GB VRAM
- **Speed:** Fast inference on 3060
- **Quality:** Excellent for analysis and reasoning
- **Context:** 128K tokens
- **Quantization:** Q4_K_M (good balance)

#### Alternative: **Phi-3 Mini**
```bash
ollama pull phi3:mini
```
- **Size:** ~2.3GB VRAM
- **Speed:** Very fast
- **Quality:** Strong reasoning, especially for code
- **Context:** 128K tokens

#### Alternative: **Mistral 7B** (if you can manage VRAM)
```bash
ollama pull mistral:7b-instruct-q4_0
```
- **Size:** ~4GB VRAM
- **Speed:** Moderate
- **Quality:** Better than 3B models
- **Note:** Might need to reduce batch size

### 2. **Embeddings - Replace Gemini Embeddings**

#### Primary Choice: **nomic-embed-text**
```bash
ollama pull nomic-embed-text
```
- **Size:** ~274MB VRAM
- **Dimensions:** 768 (same as Gemini!)
- **Speed:** Very fast
- **Quality:** Best open-source embedding model
- **Perfect match:** Drop-in replacement for Gemini

#### Alternative: **all-minilm**
```bash
ollama pull all-minilm
```
- **Size:** ~120MB VRAM
- **Dimensions:** 384
- **Speed:** Extremely fast
- **Note:** Need to update DB schema for 384 dimensions

### 3. **VRAM Budget**

With 6GB VRAM, here's what you can run simultaneously:

```
LLM (Llama 3.2 3B):     ~2.0 GB
Embeddings (nomic):     ~0.3 GB
System/OS overhead:     ~1.0 GB
Available for batch:    ~2.7 GB
-----------------------------------
Total:                  ~6.0 GB ✅
```

## 🔧 Implementation Changes

### Step 1: Install Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull models
ollama pull llama3.2:3b-instruct-q4_K_M
ollama pull nomic-embed-text
```

### Step 2: Install Python Client

```bash
uv pip install ollama
```

### Step 3: Create Local API Wrapper

Create `local_llm_api.py`:

```python
"""
Local LLM API using Ollama
Drop-in replacement for gemini_api.py
"""

import ollama
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Model configuration
LLM_MODEL = "llama3.2:3b-instruct-q4_K_M"
EMBEDDING_MODEL = "nomic-embed-text"

async def generate_embedding(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """
    Generate embeddings using local Ollama model.
    
    Returns 768-dimensional vector (same as Gemini)
    """
    try:
        response = ollama.embeddings(
            model=model,
            prompt=text
        )
        return response['embedding']
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise


async def generate_query_embedding(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """
    Generate embeddings for search queries.
    Same as generate_embedding for Ollama.
    """
    return await generate_embedding(text, model)


async def call_gemini_simple(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: str = LLM_MODEL
) -> str:
    """
    Call local LLM with Ollama.
    """
    try:
        # Build messages
        messages = []
        
        if system_instruction:
            messages.append({
                "role": "system",
                "content": system_instruction
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Call Ollama
        response = ollama.chat(
            model=model,
            messages=messages,
            options={
                "temperature": 0.7,
                "top_p": 0.9,
            }
        )
        
        return response['message']['content']
        
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        return ""


async def call_gemini_with_context(
    page_context: Dict,
    user_context: Dict,
    relevant_memories: Optional[List[Dict]] = None,
    model: str = LLM_MODEL
) -> Dict:
    """
    Analyze page with context using local LLM.
    """
    # Build prompt
    prompt = f"""Analyze this webpage and provide suggestions.

Page: {page_context.get('url')}
Title: {page_context.get('title', 'Unknown')}
User Level: {user_context.get('technical_level', 'intermediate')}

Recent memories:
{format_memories(relevant_memories) if relevant_memories else 'None'}

Provide a JSON response with:
- summary: Brief page description
- suggested_action: What the user should do
- hidden_selectors: Elements to hide
- highlight_selectors: Elements to emphasize
"""
    
    response = await call_gemini_simple(
        prompt=prompt,
        system_instruction="You are a helpful web automation assistant."
    )
    
    # Parse JSON from response
    import json
    try:
        return json.loads(response)
    except:
        return {
            "summary": response[:200],
            "suggested_action": "Review the page",
            "hidden_selectors": [],
            "highlight_selectors": []
        }


def format_memories(memories: List[Dict]) -> str:
    """Format memories for prompt."""
    if not memories:
        return "No previous interactions"
    
    lines = []
    for mem in memories[:3]:  # Top 3
        lines.append(f"- {mem.get('content', '')}")
    return "\n".join(lines)
```

### Step 4: Update Environment Variables

Add to `.env`:

```bash
# Local LLM Configuration
USE_LOCAL_LLM=true
OLLAMA_HOST=http://localhost:11434
LLM_MODEL=llama3.2:3b-instruct-q4_K_M
EMBEDDING_MODEL=nomic-embed-text

# Keep Gemini as fallback
GEMINI_API_KEY=your-key-here
TRIAL_GEMINI_TOKEN=false
```

### Step 5: Update Main Imports

In `main.py`, add conditional import:

```python
import os

USE_LOCAL = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

if USE_LOCAL:
    from local_llm_api import (
        generate_embedding,
        call_gemini_simple,
        call_gemini_with_context
    )
    print("✅ Using LOCAL LLM (Ollama)")
else:
    from gemini_api import (
        generate_embedding,
        call_gemini_simple,
        call_gemini_with_context
    )
    print("✅ Using GEMINI API (Cloud)")
```

## 📊 Performance Comparison

### Gemini (Cloud)
- **Latency:** 500-2000ms (network dependent)
- **Cost:** Free tier limits / Pay per token
- **Quality:** Excellent (1.5B+ parameters)
- **Rate Limits:** 15 req/min, 1500/day (free tier)

### Llama 3.2 3B (Local)
- **Latency:** 50-200ms (GPU dependent)
- **Cost:** Free (electricity only)
- **Quality:** Very good for 3B model
- **Rate Limits:** None (hardware only)

### nomic-embed-text (Local)
- **Latency:** 10-50ms per embedding
- **Cost:** Free
- **Quality:** Excellent (beats many larger models)
- **Dimensions:** 768 (perfect match!)

## 🎯 Optimization Tips

### 1. Batch Processing
```python
# Process multiple embeddings at once
texts = ["text1", "text2", "text3"]
embeddings = [await generate_embedding(t) for t in texts]
```

### 2. Reduce Context Window
```python
# In ollama.chat()
options={
    "num_ctx": 4096,  # Reduce from 128K to save VRAM
    "temperature": 0.7,
}
```

### 3. Use Quantized Models
```bash
# Q4_K_M is good balance (already recommended)
# For more speed, try Q4_0:
ollama pull llama3.2:3b-instruct-q4_0
```

### 4. GPU-Only Inference
```python
import ollama

# Ensure GPU usage
ollama.chat(
    model="llama3.2:3b-instruct-q4_K_M",
    messages=[...],
    options={
        "num_gpu": 1,  # Force GPU
    }
)
```

## 🧪 Testing Local Setup

```bash
# Test Ollama is running
curl http://localhost:11434/api/version

# Test LLM
ollama run llama3.2:3b-instruct-q4_K_M "Hello, how are you?"

# Test embeddings
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "test text"
}'
```

## 📈 When to Use Each Model

### Use Llama 3.2 3B if:
- ✅ You want fast responses
- ✅ Tasks are straightforward (classification, summarization)
- ✅ VRAM is limited (6GB)

### Use Mistral 7B if:
- ✅ You need better reasoning
- ✅ Complex analysis required
- ⚠️ Can manage 4-5GB VRAM for LLM

### Use Phi-3 Mini if:
- ✅ Speed is critical
- ✅ Code-related tasks
- ✅ Want Microsoft-backed model

### Use nomic-embed-text if:
- ✅ Need 768 dimensions (matches Gemini)
- ✅ Best quality embeddings
- ✅ Recommended for RAG

## 🔄 Migration Checklist

- [ ] Install Ollama
- [ ] Pull models (`llama3.2:3b-instruct-q4_K_M`, `nomic-embed-text`)
- [ ] Install Python client (`uv pip install ollama`)
- [ ] Create `local_llm_api.py`
- [ ] Update `.env` with `USE_LOCAL_LLM=true`
- [ ] Update imports in `main.py`
- [ ] Test with `ollama run llama3.2:3b-instruct-q4_K_M`
- [ ] Verify VRAM usage with `nvidia-smi`
- [ ] Run test suite

## 💡 Pro Tips

1. **Keep Gemini as Fallback**
   - If Ollama service is down, fall back to Gemini
   - Best of both worlds!

2. **Use Llama for Analysis, nomic for Embeddings**
   - This combo uses ~2.3GB VRAM total
   - Leaves plenty for batch processing

3. **Monitor VRAM**
   ```bash
   watch -n 1 nvidia-smi
   ```

4. **Preload Models**
   ```bash
   # Keep models in VRAM
   ollama run llama3.2:3b-instruct-q4_K_M --keepalive 1h
   ```

5. **Consider Model Switching**
   - Use 3B for simple tasks
   - Swap to 7B for complex analysis
   - Ollama makes this easy!

## 🚀 Expected Performance

With RTX 3060 6GB:

| Task | Model | Tokens/sec | Latency |
|------|-------|-----------|---------|
| Text Generation | Llama 3.2 3B | ~40-60 | 50-200ms |
| Embeddings | nomic-embed-text | ~1000/sec | 10-50ms |
| Page Analysis | Llama 3.2 3B | ~50 | 100-300ms |

## ❓ FAQ

**Q: Can I run Llama 3.1 8B?**
A: No, 8B models need ~5-6GB VRAM alone. Not enough room for embeddings and overhead.

**Q: What about Gemma 2B?**
A: Yes! `ollama pull gemma2:2b` - Uses only ~1.5GB, but quality is lower than Llama 3.2 3B.

**Q: Can I use CPU-only?**
A: Yes, but it will be MUCH slower (10-20x). Not recommended for production.

**Q: What about LM Studio or Koboldcpp?**
A: They work too! But Ollama has the best API compatibility and ease of use.

---

**Recommendation:** Start with `llama3.2:3b-instruct-q4_K_M` + `nomic-embed-text`. This combo is perfect for your 3060 6GB! 🚀
