"""
Local LLM API using Ollama
===========================
Drop-in replacement for gemini_api.py that uses local models
"""

import os
import logging
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

# Try to import ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("⚠️ Ollama package not installed. Install with: uv pip install ollama")

# Configuration from environment
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.2:3b-instruct-q4_K_M")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

if OLLAMA_AVAILABLE:
    # Configure Ollama client
    try:
        ollama.Client(host=OLLAMA_HOST)
        logger.info(f"✓ Ollama configured: {OLLAMA_HOST}")
        logger.info(f"  • LLM: {LLM_MODEL}")
        logger.info(f"  • Embeddings: {EMBEDDING_MODEL}")
    except Exception as e:
        logger.warning(f"⚠️ Could not connect to Ollama: {e}")


# ============================================================================
# Embedding Generation
# ============================================================================

async def generate_embedding(text: str, model: str = None) -> List[float]:
    """
    Generate embeddings using local Ollama model.
    
    Args:
        text: The text to embed
        model: Model to use (defaults to EMBEDDING_MODEL from env)
        
    Returns:
        List of floats representing the embedding vector
        
    Note: nomic-embed-text produces 768-dimensional vectors (same as Gemini!)
    """
    if not OLLAMA_AVAILABLE:
        raise ImportError("Ollama package not installed")
    
    if model is None:
        model = EMBEDDING_MODEL
    
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        response = client.embeddings(
            model=model,
            prompt=text
        )
        return response['embedding']
    except Exception as e:
        logger.error(f"Error generating embedding with Ollama: {e}")
        raise


async def generate_query_embedding(text: str, model: str = None) -> List[float]:
    """
    Generate embeddings optimized for search queries.
    
    Args:
        text: The query text to embed
        model: Model to use (defaults to EMBEDDING_MODEL from env)
        
    Returns:
        List of floats representing the embedding vector
        
    Note: For Ollama, query and document embeddings use the same model
    """
    return await generate_embedding(text, model)


# ============================================================================
# LLM Calls
# ============================================================================

async def call_gemini_simple(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: str = None
) -> str:
    """
    Simple LLM call using Ollama.
    
    Args:
        prompt: The user prompt/question
        system_instruction: Optional system instruction for the model
        model: Model to use (defaults to LLM_MODEL from env)
        
    Returns:
        Generated text response
    """
    if not OLLAMA_AVAILABLE:
        raise ImportError("Ollama package not installed")
    
    if model is None:
        model = LLM_MODEL
    
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        
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
        response = client.chat(
            model=model,
            messages=messages,
            options={
                "temperature": 0.7,
                "top_p": 0.9,
                "num_ctx": 4096,  # Context window (reduce if VRAM limited)
            }
        )
        
        return response['message']['content']
        
    except Exception as e:
        logger.error(f"Error calling Ollama LLM: {e}")
        return ""


async def call_gemini_with_context(
    page_context: Dict,
    user_context: Dict,
    relevant_memories: Optional[List[Dict]] = None,
    model: str = None
) -> Dict:
    """
    Call LLM with page context, user profile, and relevant memories.
    
    Args:
        page_context: Dictionary with url, html_content, metadata
        user_context: User profile information
        relevant_memories: List of relevant past interactions from RAG
        model: Model to use (defaults to LLM_MODEL from env)
        
    Returns:
        Dictionary with suggestions and actions
    """
    try:
        # Build the prompt
        prompt = build_analysis_prompt(page_context, user_context, relevant_memories)
        
        system_instruction = """You are a helpful web automation assistant.
Analyze webpages and provide structured JSON responses with:
- summary: Brief description
- suggested_action: What the user should do
- hidden_selectors: CSS selectors to hide
- highlight_selectors: CSS selectors to highlight

Always respond with valid JSON."""

        # Generate response
        response_text = await call_gemini_simple(
            prompt=prompt,
            system_instruction=system_instruction,
            model=model
        )
        
        # Parse the response
        result = parse_llm_response(response_text)
        
        return result
        
    except Exception as e:
        logger.error(f"Error calling Ollama with context: {e}")
        return {
            "summary": f"Error analyzing page: {str(e)}",
            "suggested_action": "Review the page manually",
            "hidden_selectors": [],
            "highlight_selectors": []
        }


def build_analysis_prompt(
    page_context: Dict,
    user_context: Dict,
    relevant_memories: Optional[List[Dict]] = None
) -> str:
    """
    Build a prompt for page analysis.
    """
    url = page_context.get('url', 'Unknown URL')
    title = page_context.get('title', 'Unknown Title')
    technical_level = user_context.get('technical_level', 'intermediate')
    
    # Format memories
    memories_text = "None"
    if relevant_memories:
        memories_text = "\n".join([
            f"- {mem.get('content', '')}"
            for mem in relevant_memories[:3]
        ])
    
    prompt = f"""Analyze this webpage and provide structured guidance.

**Page Information:**
- URL: {url}
- Title: {title}

**User Profile:**
- Technical Level: {technical_level}

**Recent Interactions:**
{memories_text}

**Task:**
Provide a JSON response with:
1. summary: Brief description of the page (1-2 sentences)
2. suggested_action: What action the user should take
3. hidden_selectors: Array of CSS selectors for elements to hide (if any)
4. highlight_selectors: Array of CSS selectors for elements to emphasize (if any)

Respond only with valid JSON, no other text."""

    return prompt


def parse_llm_response(response_text: str) -> Dict:
    """
    Parse LLM's response into structured format.
    
    Args:
        response_text: Raw text response from LLM
        
    Returns:
        Dictionary with suggestions and actions
    """
    try:
        # Try to parse as JSON
        # Sometimes LLMs wrap JSON in markdown code blocks
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        # Parse JSON
        result = json.loads(text)
        
        # Ensure required fields exist
        return {
            "summary": result.get("summary", "Page analyzed"),
            "suggested_action": result.get("suggested_action", "Review the page"),
            "hidden_selectors": result.get("hidden_selectors", []),
            "highlight_selectors": result.get("highlight_selectors", [])
        }
        
    except json.JSONDecodeError as e:
        logger.warning(f"Could not parse LLM response as JSON: {e}")
        
        # Fallback: use the text as summary
        return {
            "summary": response_text[:200] if len(response_text) > 200 else response_text,
            "suggested_action": "Review the page manually",
            "hidden_selectors": [],
            "highlight_selectors": []
        }


async def generate_chatbot_response(
    user_message: str,
    user_context: Dict,
    conversation_history: Optional[List[Dict]] = None,
    model: str = None
) -> str:
    """
    Generate a helpful chatbot response using Ollama.
    
    Args:
        user_message: The user's message
        user_context: User profile information
        conversation_history: Previous messages in the conversation
        model: Model to use (defaults to LLM_MODEL from env)
        
    Returns:
        Chatbot response string
    """
    if not OLLAMA_AVAILABLE:
        return "Ollama is not available. Please install: uv pip install ollama"
    
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        
        if model is None:
            model = LLM_MODEL
        
        # Build conversation context
        technical_level = user_context.get('technical_level', 'intermediate')
        
        messages = []
        
        # System prompt
        messages.append({
            "role": "system",
            "content": f"""You are a helpful browser automation assistant. 
The user has a {technical_level} technical level. 
Provide clear, actionable advice about web navigation and automation.
Keep responses concise and friendly."""
        })
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Generate response
        response = client.chat(
            model=model,
            messages=messages,
            options={
                "temperature": 0.8,
                "top_p": 0.9,
            }
        )
        
        return response['message']['content']
        
    except Exception as e:
        logger.error(f"Error generating chatbot response: {e}")
        return "I encountered an error. Please try again."


# ============================================================================
# Utility Functions
# ============================================================================

def check_ollama_status() -> Dict:
    """
    Check if Ollama is available and which models are installed.
    
    Returns:
        Dictionary with status information
    """
    if not OLLAMA_AVAILABLE:
        return {
            "available": False,
            "error": "Ollama package not installed",
            "models": []
        }
    
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        
        # Try to list models
        models_response = client.list()
        
        # Extract model names safely (handle both 'name' and 'model' keys)
        model_list = []
        if 'models' in models_response:
            for m in models_response['models']:
                # Try different possible keys
                model_name = m.get('name') or m.get('model') or str(m)
                model_list.append(model_name)
        
        return {
            "available": True,
            "host": OLLAMA_HOST,
            "models": model_list,
            "configured_llm": LLM_MODEL,
            "configured_embedding": EMBEDDING_MODEL
        }
        
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "models": []
        }


if __name__ == "__main__":
    # Test the Ollama connection
    import asyncio
    
    async def test():
        print("=" * 60)
        print("🧪 Testing Ollama Connection")
        print("=" * 60)
        
        # Check status
        status = check_ollama_status()
        print(f"\n📊 Status:")
        for key, value in status.items():
            print(f"   • {key}: {value}")
        
        if not status['available']:
            print("\n❌ Ollama is not available!")
            print("   Install: curl -fsSL https://ollama.com/install.sh | sh")
            print("   Then: ollama pull llama3.2:3b-instruct-q4_K_M")
            return
        
        # Test embedding
        print(f"\n🧪 Testing embedding generation...")
        try:
            embedding = await generate_embedding("Hello world")
            print(f"   ✅ Generated {len(embedding)}-dimensional embedding")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test LLM
        print(f"\n🧪 Testing LLM...")
        try:
            response = await call_gemini_simple(
                "Say hello in one sentence.",
                system_instruction="You are a friendly assistant."
            )
            print(f"   ✅ Response: {response}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Tests complete!")
        print("=" * 60)
    
    asyncio.run(test())
