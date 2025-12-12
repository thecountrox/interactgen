"""
Gemini API Integration Module
==============================
Handles LLM and embedding generation using Google's Gemini API
"""

import os
import logging
from typing import List, Dict, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✓ Gemini API configured successfully")
else:
    logger.warning("⚠️  GEMINI_API_KEY not set")


# ============================================================================
# Embedding Generation
# ============================================================================

async def generate_embedding(text: str, model: str = "models/embedding-001") -> List[float]:
    """
    Generate embeddings using Gemini's embedding model.
    
    Args:
        text: The text to embed
        model: The embedding model to use (default: embedding-001)
        
    Returns:
        List of floats representing the embedding vector
        
    Note: Gemini's embedding-001 produces 768-dimensional vectors
    """
    try:
        result = genai.embed_content(
            model=model,
            content=text,
            task_type="retrieval_document"  # Options: retrieval_query, retrieval_document, semantic_similarity
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise


async def generate_query_embedding(text: str, model: str = "models/embedding-001") -> List[float]:
    """
    Generate embeddings optimized for search queries.
    
    Args:
        text: The query text to embed
        model: The embedding model to use
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        result = genai.embed_content(
            model=model,
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Error generating query embedding: {e}")
        raise


# ============================================================================
# LLM Generation
# ============================================================================

async def call_gemini_with_context(
    page_context: Dict,
    user_context: Dict,
    relevant_memories: Optional[List[Dict]] = None,
    model: str = "gemini-1.5-flash"
) -> Dict:
    """
    Call Gemini API with page context, user profile, and relevant memories.
    
    Args:
        page_context: Dictionary with url, html_content, metadata
        user_context: User profile information
        relevant_memories: List of relevant past interactions from RAG
        model: Gemini model to use (gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash-exp)
        
    Returns:
        Dictionary with suggestions and actions
    """
    try:
        # Initialize the model
        llm = genai.GenerativeModel(model)
        
        # Build the prompt
        prompt = build_analysis_prompt(page_context, user_context, relevant_memories)
        
        # Generate response
        response = llm.generate_content(prompt)
        
        # Parse the response (you may want to use structured output or JSON mode)
        result = parse_gemini_response(response.text)
        
        return result
        
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return {
            "suggestions": [f"Error analyzing page: {str(e)}"],
            "actions": []
        }


def build_analysis_prompt(
    page_context: Dict,
    user_context: Dict,
    relevant_memories: Optional[List[Dict]] = None
) -> str:
    """
    Build a comprehensive prompt for the Judge layer.
    
    Args:
        page_context: Current page information
        user_context: User profile and preferences
        relevant_memories: Relevant past interactions
        
    Returns:
        Formatted prompt string
    """
    technical_level = user_context.get('technical_level', 'intermediate')
    personality_type = user_context.get('personality_type', 'analytical')
    
    prompt = f"""You are an intelligent browser automation assistant analyzing a webpage to help the user.

User Profile:
- Technical Level: {technical_level}
- Personality Type: {personality_type}

Current Page:
- URL: {page_context.get('url', 'Unknown')}
- Metadata: {page_context.get('metadata', {})}

"""
    
    # Add relevant memories if available
    if relevant_memories:
        prompt += "Relevant Past Interactions:\n"
        for memory in relevant_memories[:3]:  # Limit to top 3
            prompt += f"- {memory.get('content', 'N/A')}\n"
        prompt += "\n"
    
    prompt += """Based on the page context and user profile, provide:

1. **Suggestions**: 3-5 helpful tips or observations about this page
2. **Actions**: Specific UI elements to highlight or interact with

Format your response as JSON:
{
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
  "actions": [
    {"type": "highlight", "selector": "css-selector", "message": "tooltip text"},
    {"type": "click", "selector": "css-selector", "reason": "why to click"}
  ]
}
"""
    
    return prompt


def parse_gemini_response(response_text: str) -> Dict:
    """
    Parse Gemini's text response into structured format.
    
    Attempts to extract JSON if present, otherwise creates a basic structure.
    """
    try:
        # Try to find JSON in the response
        import json
        import re
        
        # Look for JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try parsing the whole response as JSON
        return json.loads(response_text)
        
    except:
        # Fallback: return the text as a suggestion
        return {
            "suggestions": [response_text.strip()],
            "actions": []
        }


async def call_gemini_simple(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: str = "gemini-1.5-flash"
) -> str:
    """
    Simple Gemini API call with just a prompt.
    
    Args:
        prompt: The user prompt/question
        system_instruction: Optional system instruction for the model
        model: Gemini model to use
        
    Returns:
        Generated text response
    """
    try:
        # Initialize the model with optional system instruction
        if system_instruction:
            llm = genai.GenerativeModel(
                model,
                system_instruction=system_instruction
            )
        else:
            llm = genai.GenerativeModel(model)
        
        # Generate response
        response = llm.generate_content(prompt)
        
        return response.text if response.text else ""
        
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return ""


def parse_gemini_response(response_text: str) -> Dict:
    """
    Parse Gemini's response into structured format.
    
    Args:
        response_text: Raw text response from Gemini
        
    Returns:
        Dictionary with suggestions and actions
    """
    import json
    import re
    
    try:
        # Try to extract JSON from the response
        # Look for JSON block in markdown code fences or raw JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            json_str = json_match.group(0) if json_match else response_text
        
        result = json.loads(json_str)
        return result
        
    except Exception as e:
        logger.warning(f"Could not parse JSON response: {e}")
        # Fallback to simple text parsing
        return {
            "suggestions": [response_text[:200]],
            "actions": []
        }


# ============================================================================
# Chatbot Functions
# ============================================================================

async def generate_chatbot_response(
    user_message: str,
    user_context: Dict,
    conversation_history: Optional[List[Dict]] = None,
    model: str = "gemini-1.5-flash"
) -> str:
    """
    Generate a helpful chatbot response using Gemini.
    
    Args:
        user_message: The user's message
        user_context: User profile information
        conversation_history: Previous messages in the conversation
        model: Gemini model to use
        
    Returns:
        Chatbot response string
    """
    try:
        llm = genai.GenerativeModel(model)
        
        # Build conversation context
        technical_level = user_context.get('technical_level', 'intermediate')
        
        system_prompt = f"""You are a helpful browser automation assistant. 
The user has a {technical_level} technical level. 
Provide clear, actionable advice about web navigation and automation.
Keep responses concise and friendly."""
        
        # Build prompt with history
        prompt = system_prompt + "\n\n"
        
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt += f"{role}: {content}\n"
        
        prompt += f"user: {user_message}\nassistant:"
        
        response = llm.generate_content(prompt)
        
        return response.text
        
    except Exception as e:
        logger.error(f"Error generating chatbot response: {e}")
        return "I'm sorry, I encountered an error processing your request."


# ============================================================================
# Batch Embedding Generation
# ============================================================================

async def generate_embeddings_batch(texts: List[str], model: str = "models/embedding-001") -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently.
    
    Args:
        texts: List of texts to embed
        model: The embedding model to use
        
    Returns:
        List of embedding vectors
    """
    try:
        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model=model,
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        
        return embeddings
        
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        raise
