# Quick Start: Local LLM with Ollama

Run your agent completely offline with local models!

## 🚀 Setup (5 minutes)

### Step 1: Install Ollama

```bash
# Linux/Mac
curl -fsSL https://ollama.com/install.sh | sh

# Or visit: https://ollama.com/download
```

### Step 2: Pull Models

```bash
# LLM for text generation (2GB)
ollama pull llama3.2:3b-instruct-q4_K_M

# Embeddings for RAG (274MB)  
ollama pull nomic-embed-text
```

### Step 3: Install Python Package

```bash
uv pip install ollama
# or: pip install ollama
```

### Step 4: Configure Environment

Edit your `.env` file:

```bash
# Enable local LLM
USE_LOCAL_LLM=true

# Ollama configuration (defaults shown)
OLLAMA_HOST=http://localhost:11434
OLLAMA_LLM_MODEL=llama3.2:3b-instruct-q4_K_M
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### Step 5: Start Server

```bash
# Start Ollama service (if not running)
ollama serve

# In another terminal, start your app
uv run main.py
```

You should see:
```
🏠 Using LOCAL LLM (Ollama)
✓ Ollama connected: http://localhost:11434
  Available models: llama3.2:3b-instruct-q4_K_M, nomic-embed-text
```

## ✅ Done!

Your agent now runs completely offline using local models!

## 🧪 Test It

```bash
# Test Ollama directly
ollama run llama3.2:3b-instruct-q4_K_M "Hello, how are you?"

# Test embeddings
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "test"
}'

# Test your API
curl http://localhost:8000/health
```

## 📊 Model Comparison

### Llama 3.2 3B vs Gemini 1.5 Flash

| Feature | Llama 3.2 3B (Local) | Gemini 1.5 Flash (Cloud) |
|---------|---------------------|-------------------------|
| **Speed** | 50-200ms | 500-2000ms |
| **Cost** | Free | Free tier limited |
| **Quality** | Very Good | Excellent |
| **Privacy** | Complete | Data sent to Google |
| **Rate Limits** | None | 15/min, 1500/day |
| **VRAM** | ~2GB | N/A |

### nomic-embed-text vs Gemini Embeddings

| Feature | nomic-embed-text | Gemini embedding-001 |
|---------|------------------|---------------------|
| **Dimensions** | 768 | 768 |
| **Speed** | 10-50ms | 100-500ms |
| **Quality** | Excellent | Excellent |
| **VRAM** | ~274MB | N/A |

## 🔄 Switching Between Local and Cloud

Simply toggle in `.env`:

```bash
# Use local models
USE_LOCAL_LLM=true

# Use cloud (Gemini)
USE_LOCAL_LLM=false
```

No code changes needed! The system automatically uses the right API.

## 💡 Tips

### 1. Keep Models in Memory

```bash
# Preload to avoid cold starts
ollama run llama3.2:3b-instruct-q4_K_M --keepalive 1h
```

### 2. Monitor VRAM Usage

```bash
watch -n 1 nvidia-smi
```

### 3. Try Different Models

```bash
# Smaller, faster (1.5GB)
ollama pull gemma2:2b
# Update .env: OLLAMA_LLM_MODEL=gemma2:2b

# Larger, better quality (4GB)
ollama pull mistral:7b-instruct-q4_0
# Update .env: OLLAMA_LLM_MODEL=mistral:7b-instruct-q4_0
```

### 4. Use Cloud as Fallback

Keep both configured:

```bash
# Local models (primary)
USE_LOCAL_LLM=true
OLLAMA_HOST=http://localhost:11434

# Gemini API (fallback)
GEMINI_API_KEY=your-key-here
```

If Ollama is down, manually switch to cloud.

## 🐛 Troubleshooting

### "Connection refused"

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# If not, start it
ollama serve
```

### "Model not found"

```bash
# List installed models
ollama list

# Pull missing model
ollama pull llama3.2:3b-instruct-q4_K_M
```

### Server shows "Ollama not available"

```bash
# Install Python package
uv pip install ollama

# Restart server
uv run main.py
```

### Out of VRAM

```bash
# Use smaller model
ollama pull gemma2:2b

# Or reduce context window in ollama_api.py:
# options={ "num_ctx": 2048 }  # Instead of 4096
```

## 📚 More Models

Browse all available models:
https://ollama.com/library

**Recommended for RTX 3060 6GB:**
- `llama3.2:3b-instruct-q4_K_M` - Best balanced
- `phi3:mini` - Fast, code-focused
- `gemma2:2b` - Smallest, fastest
- `nomic-embed-text` - Best embeddings

## 🎯 Performance on RTX 3060 6GB

With recommended models:

```
Task: Page Analysis
Model: Llama 3.2 3B
Tokens/sec: 40-60
Latency: 50-200ms
Total VRAM: ~2.3GB (with embeddings)

Task: Embedding Generation  
Model: nomic-embed-text
Embeddings/sec: ~1000
Latency: 10-50ms

Total system usage: ~3GB VRAM
Remaining: ~3GB for batching
```

## ✨ Benefits

✅ **No API costs** - completely free  
✅ **No rate limits** - unlimited requests  
✅ **Privacy** - data never leaves your machine  
✅ **Low latency** - 5-10x faster than cloud  
✅ **Offline capable** - works without internet  
✅ **Same dimensions** - nomic = 768 (like Gemini)

---

**Ready to go offline? Set `USE_LOCAL_LLM=true` and enjoy! 🚀**
