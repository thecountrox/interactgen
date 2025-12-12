"""
Judge Engine - The Brain of the Browser Automation Agent
========================================================
Uses LLM + RAG to analyze pages and make intelligent decisions about UI modifications
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from supabase import Client
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Conditional LLM/Embedding API import based on USE_LOCAL_LLM
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

if USE_LOCAL_LLM:
    from utils.ollama_api import generate_embedding, call_gemini_simple

    logger.info("🏠 Judge Engine using LOCAL LLM (Ollama)")
else:
    from utils.gemini_api import generate_embedding, call_gemini_simple

    logger.info("☁️  Judge Engine using CLOUD LLM (Gemini API)")

# ============================================================================
# Helper Functions
# ============================================================================


def extract_page_summary(html: str, max_length: int = 500) -> str:
    """
    Extract a clean text summary from HTML for embedding generation.
    Removes scripts, styles, and excessive whitespace.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()

        # Get text
        text = soup.get_text(separator=" ", strip=True)

        # Collapse whitespace
        text = " ".join(text.split())

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "..."

        return text
    except Exception as e:
        logger.error(f"Error extracting page summary: {e}")
        return html[:max_length]


def extract_key_elements(html: str) -> Dict[str, Any]:
    """
    Extract key structural elements from HTML to help the Judge understand the page.
    Returns forms, buttons, links, headings, etc.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")

        elements = {
            "title": soup.title.string if soup.title else None,
            "forms": len(soup.find_all("form")),
            "buttons": len(soup.find_all(["button", 'input[type="submit"]'])),
            "links": len(soup.find_all("a")),
            "headings": [
                h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])[:5]
            ],
            "inputs": len(soup.find_all(["input", "textarea", "select"])),
            "images": len(soup.find_all("img")),
        }

        return elements
    except Exception as e:
        logger.error(f"Error extracting key elements: {e}")
        return {}


# ============================================================================
# RAG - Memory Retrieval
# ============================================================================


async def retrieve_relevant_memories(
    supabase: Client, user_id: str, html_content: str, top_k: int = 3
) -> List[Dict]:
    """
    Step 1 (RAG): Query the memories table for the most relevant past interactions.

    Uses vector similarity search to find memories related to the current page context.
    """
    try:
        # Extract page summary for embedding
        page_summary = extract_page_summary(html_content)

        # Generate embedding for the current page
        logger.info(f"Generating embedding for page summary...")
        query_embedding = await generate_embedding(page_summary)

        if not query_embedding:
            logger.warning("Failed to generate embedding, returning empty memories")
            return []

        # Query Supabase for similar memories using the search_memories function
        logger.info(f"Searching for top {top_k} relevant memories for user {user_id}")

        result = supabase.rpc(
            "search_memories",
            {
                "query_embedding": query_embedding,
                "match_user_id": user_id,
                "match_threshold": 0.5,  # Minimum similarity threshold
                "match_count": top_k,
            },
        ).execute()

        if result.data:
            logger.info(f"✓ Found {len(result.data)} relevant memories")
            return result.data
        else:
            logger.info("No relevant memories found")
            return []

    except Exception as e:
        logger.error(f"Error retrieving memories: {e}")
        # Return mock data for development/testing
        logger.info("Using mock memory data for development")
        return [
            {
                "content": "User previously visited a login page",
                "similarity": 0.85,
                "created_at": "2025-12-10T10:00:00Z",
            },
            {
                "content": "User filled out a contact form",
                "similarity": 0.72,
                "created_at": "2025-12-11T15:30:00Z",
            },
        ]


# ============================================================================
# Judge Engine - Main Logic
# ============================================================================


async def evaluate_page(
    html: str,
    user_id: str,
    supabase: Client,
    url: Optional[str] = None,
    user_context: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    The main Judge function that analyzes a page and returns actionable decisions.

    Process:
    1. Extract page structure and content
    2. Retrieve relevant memories via RAG
    3. Build context for LLM
    4. Call Gemini to generate decisions
    5. Return structured JSON response

    Args:
        html: The HTML content of the page
        user_id: UUID of the user
        supabase: Supabase client instance
        url: Optional URL of the page
        user_context: Optional user profile data (technical_level, personality_type)

    Returns:
        Dict with keys: summary, hidden_selectors, highlight_selectors, suggested_action
    """

    try:
        logger.info(f"🧠 Judge Engine: Evaluating page for user {user_id}")

        # Step 1: Extract page structure
        page_elements = extract_key_elements(html)
        page_text = extract_page_summary(html, max_length=1000)

        logger.info(f"Page elements: {page_elements}")

        # Step 2 (RAG): Retrieve relevant memories
        relevant_memories = await retrieve_relevant_memories(
            supabase=supabase, user_id=user_id, html_content=html, top_k=3
        )

        # Format memories for the prompt
        memory_context = (
            "\n".join(
                [
                    f"- {mem.get('content', 'N/A')} (similarity: {mem.get('similarity', 0):.2f})"
                    for mem in relevant_memories
                ]
            )
            if relevant_memories
            else "No previous interactions found."
        )

        # Get user profile info
        if not user_context:
            try:
                user_profile = (
                    supabase.table("profiles").select("*").eq("id", user_id).execute()
                )
                user_context = user_profile.data[0] if user_profile.data else {}
            except:
                user_context = {}

        technical_level = user_context.get("technical_level", "intermediate")
        personality_type = user_context.get("personality_type", "analytical")

        # Step 3: Construct the prompt for Gemini
        system_prompt = f"""You are a UX personalization engine for a browser automation assistant.

Your role is to analyze web pages and provide intelligent suggestions to improve the user's experience.

User Profile:
- Technical Level: {technical_level}
- Personality Type: {personality_type}

User's History:
{memory_context}

Based on this context and the page structure provided, analyze the page and return a JSON object with your recommendations."""

        user_prompt = f"""Analyze this web page and provide personalized UX recommendations.

URL: {url or "Unknown"}

Page Structure:
- Title: {page_elements.get("title", "N/A")}
- Forms: {page_elements.get("forms", 0)}
- Buttons: {page_elements.get("buttons", 0)}
- Links: {page_elements.get("links", 0)}
- Input fields: {page_elements.get("inputs", 0)}
- Key headings: {", ".join(page_elements.get("headings", [])[:3])}

Page Content Summary:
{page_text}

Return a JSON object with this EXACT structure:
{{
    "summary": "A 1-sentence description of what this page is for",
    "hidden_selectors": ["list of CSS selectors for clutter/distractions to hide"],
    "highlight_selectors": ["list of CSS selectors for important elements to highlight"],
    "suggested_action": "The next logical step the user should take (optional)"
}}

Guidelines:
- For beginners: Hide advanced options, highlight primary actions
- For experts: Keep technical details, hide tutorial content
- Consider the user's past behavior from their history
- Be specific with CSS selectors (use classes, IDs, or element types)
- Suggested action should be clear and actionable

Return ONLY valid JSON, no additional text."""

        # Step 4: Call Gemini API
        logger.info("Calling Gemini API for page analysis...")

        response = await call_gemini_simple(
            prompt=user_prompt, system_instruction=system_prompt
        )

        if not response:
            logger.warning("Gemini API returned empty response, using fallback")
            return create_fallback_response(page_elements, technical_level)

        # Step 5: Parse and validate the response
        try:
            # Extract JSON from response (handle markdown code blocks if present)
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)

            # Validate required fields
            required_fields = ["summary", "hidden_selectors", "highlight_selectors"]
            for field in required_fields:
                if field not in result:
                    result[field] = [] if "selectors" in field else "Analysis complete"

            logger.info(
                f"✓ Judge Engine evaluation complete: {result.get('summary', 'N/A')}"
            )
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.debug(f"Raw response: {response}")
            return create_fallback_response(page_elements, technical_level)

    except Exception as e:
        logger.error(f"Error in evaluate_page: {e}", exc_info=True)
        return create_fallback_response({}, "intermediate")


def create_fallback_response(
    page_elements: Dict, technical_level: str = "intermediate"
) -> Dict[str, Any]:
    """
    Create a safe fallback response when LLM fails.
    """
    has_forms = page_elements.get("forms", 0) > 0
    has_buttons = page_elements.get("buttons", 0) > 0

    # Basic heuristics
    hidden_selectors = []
    highlight_selectors = []

    if technical_level == "beginner":
        hidden_selectors = [".advanced-settings", ".developer-options", ".debug-panel"]
        highlight_selectors = [
            "button[type='submit']",
            ".primary-button",
            ".cta-button",
        ]
    elif technical_level == "expert":
        hidden_selectors = [".tutorial", ".help-text", ".beginner-tip"]
        highlight_selectors = [".api-documentation", ".advanced-options", "code"]

    suggested_action = None
    if has_forms and has_buttons:
        suggested_action = "Fill out the form and click the submit button"
    elif has_buttons:
        suggested_action = "Click the primary action button"

    return {
        "summary": f"Page contains {page_elements.get('forms', 0)} forms and {page_elements.get('buttons', 0)} buttons",
        "hidden_selectors": hidden_selectors,
        "highlight_selectors": highlight_selectors,
        "suggested_action": suggested_action,
    }


# ============================================================================
# Memory Storage (for future learning)
# ============================================================================


async def store_interaction_memory(
    supabase: Client,
    user_id: str,
    page_url: str,
    page_content: str,
    user_action: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> bool:
    """
    Store a new interaction in the memories table with embedding.
    This builds up the RAG knowledge base over time.
    """
    try:
        # Create a meaningful content description
        content = f"User visited {page_url}"
        if user_action:
            content += f" and {user_action}"

        # Generate embedding
        embedding = await generate_embedding(content)

        if not embedding:
            logger.error("Failed to generate embedding for memory storage")
            return False

        # Prepare metadata
        memory_metadata = {
            "url": page_url,
            "action": user_action,
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }

        # Insert into memories table
        result = (
            supabase.table("memories")
            .insert(
                {
                    "user_id": user_id,
                    "content": content,
                    "embedding": embedding,
                    "metadata": memory_metadata,
                }
            )
            .execute()
        )

        if result.data:
            logger.info(f"✓ Stored interaction memory for user {user_id}")
            return True
        else:
            logger.error("Failed to store memory in database")
            return False

    except Exception as e:
        logger.error(f"Error storing interaction memory: {e}")
        return False


# ============================================================================
# Utility Functions
# ============================================================================


def validate_css_selector(selector: str) -> bool:
    """
    Basic validation for CSS selectors to prevent injection attacks.
    """
    # Simple check - in production, use a proper CSS parser
    dangerous_chars = [";", "{", "}", "<", ">", "javascript:", "eval("]
    return not any(char in selector.lower() for char in dangerous_chars)


def sanitize_selectors(selectors: List[str]) -> List[str]:
    """
    Sanitize and validate CSS selectors before returning them to the client.
    """
    return [s for s in selectors if validate_css_selector(s)]
