"""
Tertiary Chat Layer - The Proactive Tutor
=========================================
Runs in the background to provide contextual tips and knowledge gap assistance.

This module analyzes page content and user profiles to identify learning opportunities
and sends proactive nudges via WebSocket.
"""

import os
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Conditional LLM/Embedding API import based on USE_LOCAL_LLM
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

if USE_LOCAL_LLM:
    from utils.ollama_api import call_gemini_simple

    logger.info("🏠 Tertiary Chat using LOCAL LLM (Ollama)")
else:
    from utils.gemini_api import call_gemini_simple

    logger.info("☁️  Tertiary Chat using CLOUD LLM (Gemini API)")

# ============================================================================
# Knowledge Gap Detection
# ============================================================================


def detect_page_complexity(html: str) -> Dict[str, Any]:
    """
    Analyze HTML to determine page complexity and technical concepts.

    Returns:
        Dict with complexity_level, detected_concepts, and page_type
    """
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Extract text content
        text = soup.get_text(separator=" ", strip=True).lower()
        title = soup.title.string.lower() if soup.title else ""

        # Detect technical concepts and keywords
        technical_keywords = {
            "beginner": [
                "tutorial",
                "introduction",
                "getting started",
                "basics",
                "learn",
                "guide",
            ],
            "intermediate": [
                "configuration",
                "setup",
                "api",
                "integration",
                "documentation",
            ],
            "advanced": [
                "optimization",
                "performance",
                "architecture",
                "advanced",
                "algorithm",
                "scaling",
                "distributed",
                "concurrent",
                "async",
            ],
            "expert": [
                "internals",
                "low-level",
                "compiler",
                "kernel",
                "protocol",
                "specification",
                "rfc",
                "implementation details",
                "source code",
            ],
        }

        # Programming concepts
        programming_concepts = {
            "react": [
                "react",
                "jsx",
                "component",
                "hook",
                "useeffect",
                "usestate",
                "props",
            ],
            "backend": [
                "api",
                "database",
                "server",
                "endpoint",
                "rest",
                "graphql",
                "sql",
            ],
            "devops": [
                "docker",
                "kubernetes",
                "deployment",
                "ci/cd",
                "pipeline",
                "container",
            ],
            "security": [
                "authentication",
                "authorization",
                "encryption",
                "oauth",
                "jwt",
                "security",
            ],
            "data": [
                "machine learning",
                "ai",
                "neural network",
                "model",
                "training",
                "dataset",
            ],
        }

        # Determine complexity level
        complexity_scores = {}
        for level, keywords in technical_keywords.items():
            score = sum(
                1 for keyword in keywords if keyword in text or keyword in title
            )
            complexity_scores[level] = score

        detected_level = max(complexity_scores, key=complexity_scores.get)

        # Detect specific concepts
        detected_concepts = []
        for concept, keywords in programming_concepts.items():
            if any(keyword in text or keyword in title for keyword in keywords):
                detected_concepts.append(concept)

        # Detect page type
        has_form = len(soup.find_all("form")) > 0
        has_code = len(soup.find_all(["code", "pre"])) > 0
        has_video = len(soup.find_all(["video", "iframe"])) > 0

        page_type = "general"
        if has_code and "tutorial" in text:
            page_type = "tutorial"
        elif has_code:
            page_type = "documentation"
        elif has_form:
            page_type = "form"
        elif has_video:
            page_type = "media"

        return {
            "complexity_level": detected_level,
            "complexity_score": complexity_scores[detected_level],
            "detected_concepts": detected_concepts,
            "page_type": page_type,
            "has_code_examples": has_code,
            "has_forms": has_form,
        }

    except Exception as e:
        logger.error(f"Error detecting page complexity: {e}")
        return {
            "complexity_level": "intermediate",
            "complexity_score": 0,
            "detected_concepts": [],
            "page_type": "general",
            "has_code_examples": False,
            "has_forms": False,
        }


# ============================================================================
# Proactive Nudge Generation
# ============================================================================


async def generate_proactive_nudge(
    html_summary: str, user_profile: Dict[str, Any], page_url: Optional[str] = None
) -> Optional[str]:
    """
    Generate a proactive, context-aware nudge for the user.

    This function analyzes the knowledge gap between the user's level and
    the page complexity, then generates a helpful tip or warning.

    Args:
        html_summary: Summary or full HTML of the page
        user_profile: Dict with 'technical_level', 'personality_type', etc.
        page_url: Optional URL for context

    Returns:
        A friendly nudge message, or None if no nudge is needed
    """
    try:
        # Extract user info
        user_level = user_profile.get("technical_level", "intermediate")
        personality = user_profile.get("personality_type", "analytical")
        username = user_profile.get("username", "there")

        # Analyze page complexity
        page_analysis = detect_page_complexity(html_summary)
        page_level = page_analysis["complexity_level"]
        concepts = page_analysis["detected_concepts"]
        page_type = page_analysis["page_type"]

        logger.info(
            f"📊 Page analysis: {page_level} level, concepts: {concepts}, type: {page_type}"
        )
        logger.info(f"👤 User level: {user_level}")

        # Check for knowledge gap
        level_hierarchy = ["beginner", "intermediate", "advanced", "expert"]
        user_level_idx = (
            level_hierarchy.index(user_level) if user_level in level_hierarchy else 1
        )
        page_level_idx = (
            level_hierarchy.index(page_level) if page_level in level_hierarchy else 1
        )

        gap = page_level_idx - user_level_idx

        # Decide if we need to generate a nudge
        needs_nudge = False
        nudge_type = "neutral"

        if gap >= 2:
            # Page is too advanced
            needs_nudge = True
            nudge_type = "simplify"
        elif gap == 1:
            # Slight challenge - encourage
            needs_nudge = True
            nudge_type = "encourage"
        elif gap <= -2:
            # Page might be too basic
            needs_nudge = True
            nudge_type = "suggest_advanced"
        elif page_type == "tutorial" and user_level in ["advanced", "expert"]:
            # Expert on tutorial page
            needs_nudge = True
            nudge_type = "skip_basics"
        elif page_analysis["has_forms"] and user_level == "beginner":
            # Beginner on form page
            needs_nudge = True
            nudge_type = "form_help"

        if not needs_nudge:
            logger.info("✓ No knowledge gap detected, no nudge needed")
            return None

        # Generate contextual nudge using Gemini
        logger.info(f"🤖 Generating {nudge_type} nudge...")

        nudge = await generate_nudge_with_llm(
            user_level=user_level,
            user_personality=personality,
            username=username,
            page_level=page_level,
            concepts=concepts,
            page_type=page_type,
            nudge_type=nudge_type,
            page_url=page_url,
        )

        return nudge

    except Exception as e:
        logger.error(f"Error generating proactive nudge: {e}")
        return None


async def generate_nudge_with_llm(
    user_level: str,
    user_personality: str,
    username: str,
    page_level: str,
    concepts: List[str],
    page_type: str,
    nudge_type: str,
    page_url: Optional[str],
) -> str:
    """
    Use Gemini LLM to generate a personalized, friendly nudge.
    Uses a fast model for quick responses.
    """

    # Map nudge types to instructions
    nudge_instructions = {
        "simplify": f"This page is {page_level} level but the user is {user_level}. Gently warn them this might be complex and suggest simpler alternatives or concepts to learn first.",
        "encourage": f"This page is slightly above the user's level ({user_level} → {page_level}). Encourage them that it's a good learning opportunity.",
        "suggest_advanced": f"This page might be too basic for a {user_level} user. Suggest they skip to more advanced sections or resources.",
        "skip_basics": f"Expert user on a tutorial page. Suggest they can skip the basics and jump to advanced topics.",
        "form_help": "Beginner user on a form page. Offer helpful tips about filling out forms safely and correctly.",
    }

    instruction = nudge_instructions.get(
        nudge_type, "Provide a helpful tip about this page."
    )
    concepts_str = ", ".join(concepts) if concepts else "general web content"

    system_prompt = f"""You are a friendly, proactive tutor chatbot embedded in a browser extension.

Your role is to help users navigate the web based on their skill level.

User Profile:
- Name: {username}
- Technical Level: {user_level}
- Personality: {user_personality}

Page Context:
- Complexity: {page_level}
- Type: {page_type}
- Topics: {concepts_str}
- URL: {page_url or "N/A"}

Task: {instruction}

Guidelines:
- Be friendly and encouraging, never condescending
- Keep it SHORT (1-2 sentences max, like a notification)
- Use emojis sparingly (max 1-2)
- Be actionable - give specific advice
- Match the user's personality ({user_personality})
- Use casual, conversational tone

Examples of good nudges:
- "👋 This React Hooks guide assumes you know basic components. Want me to find a simpler intro first?"
- "💡 You're ready for this! Advanced patterns can seem tricky but you've got the foundation."
- "⚡ This tutorial covers basics you probably know. Jump to the 'Advanced Patterns' section below."
"""

    user_prompt = f"Generate a short, friendly nudge message for this situation. Return ONLY the message text, no quotes or formatting."

    try:
        response = await call_gemini_simple(
            prompt=user_prompt, system_instruction=system_prompt
        )

        if response:
            # Clean up the response
            nudge = response.strip().strip('"').strip("'")
            logger.info(f"✓ Generated nudge: {nudge}")
            return nudge
        else:
            # Fallback to template-based nudge
            return generate_fallback_nudge(user_level, page_level, nudge_type, username)

    except Exception as e:
        logger.error(f"Error calling LLM for nudge: {e}")
        return generate_fallback_nudge(user_level, page_level, nudge_type, username)


def generate_fallback_nudge(
    user_level: str, page_level: str, nudge_type: str, username: str
) -> str:
    """
    Generate a simple template-based nudge when LLM fails.
    """
    templates = {
        "simplify": f"👋 Hey {username}, this page looks pretty advanced. Want me to find something more beginner-friendly?",
        "encourage": f"💡 Great choice! This is a good next step for your {user_level} level.",
        "suggest_advanced": f"⚡ {username}, you might want to skip to the advanced sections - this intro is probably too basic for you.",
        "skip_basics": f"💫 Expert tip: Feel free to jump past the basics here!",
        "form_help": f"📝 {username}, take your time with this form. I can help if you get stuck!",
    }

    return templates.get(
        nudge_type, f"👋 {username}, I'm here to help if you need anything!"
    )


# ============================================================================
# WebSocket Push Integration
# ============================================================================


async def push_nudge_to_websocket(
    connection_manager, client_id: str, nudge_message: str, priority: str = "normal"
) -> bool:
    """
    Push a proactive nudge to a specific WebSocket connection.

    Args:
        connection_manager: The ConnectionManager instance from main.py
        client_id: The WebSocket client ID (usually user_id)
        nudge_message: The message to send
        priority: 'low', 'normal', or 'high'

    Returns:
        True if message was sent successfully, False otherwise
    """
    try:
        if client_id not in connection_manager.active_connections:
            logger.info(f"Client {client_id} not connected via WebSocket")
            return False

        # Format the message with metadata
        message_payload = {
            "type": "proactive_nudge",
            "message": nudge_message,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat(),
            "dismissible": True,
        }

        # Send via connection manager
        websocket = connection_manager.active_connections[client_id]
        await websocket.send_json(message_payload)

        logger.info(f"✓ Nudge sent to {client_id}: {nudge_message[:50]}...")
        return True

    except Exception as e:
        logger.error(f"Error pushing nudge to WebSocket: {e}")
        return False


async def analyze_and_nudge(
    connection_manager,
    user_id: str,
    html_content: str,
    user_profile: Dict[str, Any],
    page_url: Optional[str] = None,
) -> bool:
    """
    Complete flow: Analyze page, generate nudge if needed, and push to WebSocket.

    This is the main function to call from your background tasks or endpoints.

    Args:
        connection_manager: ConnectionManager instance from main.py
        user_id: User's UUID (also used as WebSocket client_id)
        html_content: Full HTML of the page
        user_profile: User's profile dict (technical_level, personality_type, etc.)
        page_url: Optional URL for context

    Returns:
        True if a nudge was sent, False if no nudge was needed or sending failed
    """
    try:
        logger.info(f"🔍 Analyzing page for proactive nudges (user: {user_id})")

        # Generate nudge
        nudge = await generate_proactive_nudge(
            html_summary=html_content, user_profile=user_profile, page_url=page_url
        )

        if not nudge:
            logger.info("No nudge needed for this page")
            return False

        # Push to WebSocket
        success = await push_nudge_to_websocket(
            connection_manager=connection_manager,
            client_id=user_id,
            nudge_message=nudge,
            priority="normal",
        )

        return success

    except Exception as e:
        logger.error(f"Error in analyze_and_nudge: {e}")
        return False


# ============================================================================
# Chatbot Query Handler
# ============================================================================


async def handle_chat_query(
    user_message: str, user_profile: Dict[str, Any], page_context: Optional[Dict] = None
) -> str:
    """
    Handle direct chat queries from the user via WebSocket.

    This is for when the user explicitly asks a question, not proactive nudges.

    Args:
        user_message: The user's question
        user_profile: User profile dict
        page_context: Optional context about the current page

    Returns:
        A helpful response message
    """
    try:
        username = user_profile.get("username", "there")
        technical_level = user_profile.get("technical_level", "intermediate")

        # Build context
        context_str = ""
        if page_context:
            context_str = f"\n\nCurrent page context:\n- URL: {page_context.get('url', 'N/A')}\n- Type: {page_context.get('type', 'unknown')}"

        system_prompt = f"""You are a helpful browser assistant chatbot.

User Profile:
- Name: {username}
- Technical Level: {technical_level}

You're helping them navigate and understand web pages. Be friendly, concise, and helpful.{context_str}

Keep responses SHORT (2-3 sentences max) unless the user asks for detailed explanation."""

        user_prompt = (
            f"User question: {user_message}\n\nProvide a helpful, concise response."
        )

        response = await call_gemini_simple(
            prompt=user_prompt, system_instruction=system_prompt
        )

        if response:
            return response.strip()
        else:
            return f"I'm here to help, {username}! Could you rephrase that question?"

    except Exception as e:
        logger.error(f"Error handling chat query: {e}")
        return "Sorry, I encountered an error. Please try again!"
