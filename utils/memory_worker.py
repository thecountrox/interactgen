"""
Memory Worker - Background Learning System
==========================================
Processes user interactions and stores them as memories for RAG.

This module handles the background task of converting interactions into
embeddings and storing them in Supabase for future similarity search.
"""

import os
import logging
from typing import Dict, Optional, Any
from datetime import datetime
from uuid import UUID

from supabase import Client

logger = logging.getLogger(__name__)

# Conditional LLM/Embedding API import based on USE_LOCAL_LLM
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

if USE_LOCAL_LLM:
    from utils.ollama_api import generate_embedding

    logger.info("🏠 Memory Worker using LOCAL LLM (Ollama)")
else:
    from utils.gemini_api import generate_embedding

    logger.info("☁️  Memory Worker using CLOUD LLM (Gemini API)")

# ============================================================================
# Memory Processing
# ============================================================================


async def process_memory_background(
    user_id: str,
    interaction_summary: str,
    supabase: Client,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Background task to process and store a user interaction as a memory.

    This function is designed to be called as a FastAPI BackgroundTask.
    It generates an embedding and stores it in Supabase for future RAG queries.

    Args:
        user_id: UUID of the user (as string)
        interaction_summary: Text description of the interaction
        supabase: Supabase client instance
        metadata: Optional metadata (URL, action, timestamp, etc.)

    Returns:
        True if memory was stored successfully, False otherwise

    Example:
        ```python
        background_tasks.add_task(
            process_memory_background,
            user_id="550e8400-e29b-41d4-a716-446655440000",
            interaction_summary="User filled out contact form on example.com",
            supabase=supabase,
            metadata={"url": "https://example.com/contact", "action": "form_submission"}
        )
        ```
    """
    try:
        logger.info(
            f"🧠 Processing memory for user {user_id}: {interaction_summary[:100]}..."
        )

        # Step 1: Generate embedding using Gemini
        logger.info("Generating embedding vector...")
        embedding = await generate_embedding(interaction_summary)

        if not embedding:
            logger.error("Failed to generate embedding - cannot store memory")
            return False

        logger.info(f"✓ Generated {len(embedding)}-dimensional embedding")

        # Step 2: Prepare memory data
        memory_data = {
            "user_id": user_id,
            "content": interaction_summary,
            "embedding": embedding,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }

        # Step 3: Insert into Supabase memories table
        logger.info("Storing memory in database...")
        result = supabase.table("memories").insert(memory_data).execute()

        if result.data:
            memory_id = result.data[0].get("id", "unknown")
            logger.info(f"✅ Memory stored successfully (ID: {memory_id})")
            return True
        else:
            logger.error("Failed to insert memory into database")
            return False

    except Exception as e:
        logger.error(f"❌ Error processing memory: {e}", exc_info=True)
        return False


async def process_interaction_memory(
    user_id: str,
    url: str,
    action: str,
    supabase: Client,
    page_title: Optional[str] = None,
    html_summary: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> bool:
    """
    Process a complete interaction (page visit + action) and store as memory.

    Creates a human-readable summary and stores it with appropriate metadata.

    Args:
        user_id: UUID of the user
        url: URL of the page
        action: Description of what the user did
        supabase: Supabase client
        page_title: Optional page title
        html_summary: Optional summary of page content
        metadata: Additional metadata

    Returns:
        True if successfully stored

    Example:
        ```python
        await process_interaction_memory(
            user_id="user-123",
            url="https://example.com/login",
            action="successfully logged in",
            supabase=supabase,
            page_title="Login Page",
            metadata={"form_fields": ["email", "password"]}
        )
        ```
    """
    try:
        # Build a descriptive summary
        summary_parts = [f"User visited {url}"]

        if page_title:
            summary_parts.append(f"(page: {page_title})")

        if action:
            summary_parts.append(f"and {action}")

        if html_summary:
            summary_parts.append(f"Page contained: {html_summary[:200]}")

        interaction_summary = " ".join(summary_parts)

        # Prepare metadata
        full_metadata = {
            "url": url,
            "action": action,
            "page_title": page_title,
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }

        # Process and store
        return await process_memory_background(
            user_id=user_id,
            interaction_summary=interaction_summary,
            supabase=supabase,
            metadata=full_metadata,
        )

    except Exception as e:
        logger.error(f"Error processing interaction memory: {e}")
        return False


# ============================================================================
# Batch Memory Processing
# ============================================================================


async def process_multiple_memories(
    memories: list[Dict[str, Any]], supabase: Client
) -> Dict[str, Any]:
    """
    Process multiple memories in batch (useful for bulk imports or migrations).

    Args:
        memories: List of memory dicts with 'user_id', 'content', and optional 'metadata'
        supabase: Supabase client

    Returns:
        Dict with 'success_count', 'failed_count', and 'details'

    Example:
        ```python
        memories = [
            {
                "user_id": "user-1",
                "content": "User searched for Python tutorials",
                "metadata": {"search_query": "python basics"}
            },
            {
                "user_id": "user-2",
                "content": "User completed signup form",
                "metadata": {"form_type": "registration"}
            }
        ]

        result = await process_multiple_memories(memories, supabase)
        print(f"Stored {result['success_count']} memories")
        ```
    """
    results = {"success_count": 0, "failed_count": 0, "details": []}

    for i, memory in enumerate(memories):
        try:
            user_id = memory.get("user_id")
            content = memory.get("content")
            metadata = memory.get("metadata")

            if not user_id or not content:
                logger.warning(f"Skipping memory {i}: missing user_id or content")
                results["failed_count"] += 1
                results["details"].append(
                    {"index": i, "status": "failed", "reason": "missing_fields"}
                )
                continue

            success = await process_memory_background(
                user_id=user_id,
                interaction_summary=content,
                supabase=supabase,
                metadata=metadata,
            )

            if success:
                results["success_count"] += 1
                results["details"].append({"index": i, "status": "success"})
            else:
                results["failed_count"] += 1
                results["details"].append(
                    {"index": i, "status": "failed", "reason": "processing_error"}
                )

        except Exception as e:
            logger.error(f"Error processing memory {i}: {e}")
            results["failed_count"] += 1
            results["details"].append(
                {"index": i, "status": "failed", "reason": str(e)}
            )

    logger.info(
        f"Batch processing complete: {results['success_count']} success, {results['failed_count']} failed"
    )
    return results


# ============================================================================
# Memory Retrieval and Analysis
# ============================================================================


async def get_user_memory_stats(user_id: str, supabase: Client) -> Dict[str, Any]:
    """
    Get statistics about a user's stored memories.

    Args:
        user_id: UUID of the user
        supabase: Supabase client

    Returns:
        Dict with memory count, date range, and top actions
    """
    try:
        # Get all memories for user
        result = supabase.table("memories").select("*").eq("user_id", user_id).execute()

        if not result.data:
            return {
                "user_id": user_id,
                "total_memories": 0,
                "message": "No memories found for this user",
            }

        memories = result.data

        # Calculate stats
        stats = {
            "user_id": user_id,
            "total_memories": len(memories),
            "oldest_memory": min(m.get("created_at", "") for m in memories),
            "newest_memory": max(m.get("created_at", "") for m in memories),
            "actions": {},
        }

        # Count actions
        for memory in memories:
            metadata = memory.get("metadata", {})
            action = metadata.get("action", "unknown")
            stats["actions"][action] = stats["actions"].get(action, 0) + 1

        return stats

    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return {"user_id": user_id, "error": str(e)}


async def search_user_memories(
    user_id: str, query: str, supabase: Client, top_k: int = 5, threshold: float = 0.7
) -> list[Dict[str, Any]]:
    """
    Search a user's memories using semantic similarity.

    Args:
        user_id: UUID of the user
        query: Search query (will be embedded)
        supabase: Supabase client
        top_k: Number of results to return
        threshold: Minimum similarity threshold (0-1)

    Returns:
        List of relevant memories with similarity scores

    Example:
        ```python
        memories = await search_user_memories(
            user_id="user-123",
            query="login forms",
            supabase=supabase,
            top_k=3
        )

        for memory in memories:
            print(f"{memory['similarity']:.2f}: {memory['content']}")
        ```
    """
    try:
        # Generate embedding for query
        logger.info(f"Searching memories for: {query}")
        query_embedding = await generate_embedding(query)

        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []

        # Call Supabase RPC function
        result = supabase.rpc(
            "search_memories",
            {
                "query_embedding": query_embedding,
                "match_user_id": user_id,
                "match_threshold": threshold,
                "match_count": top_k,
            },
        ).execute()

        if result.data:
            logger.info(f"Found {len(result.data)} relevant memories")
            return result.data
        else:
            logger.info("No relevant memories found")
            return []

    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        return []


# ============================================================================
# Memory Cleanup and Maintenance
# ============================================================================


async def cleanup_old_memories(
    user_id: str, supabase: Client, days_to_keep: int = 90
) -> int:
    """
    Remove old memories to manage storage and keep data fresh.

    Args:
        user_id: UUID of the user
        supabase: Supabase client
        days_to_keep: Keep memories from the last N days

    Returns:
        Number of memories deleted
    """
    try:
        from datetime import timedelta

        cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()

        # Delete old memories
        result = (
            supabase.table("memories")
            .delete()
            .eq("user_id", user_id)
            .lt("created_at", cutoff_date)
            .execute()
        )

        deleted_count = len(result.data) if result.data else 0
        logger.info(f"Deleted {deleted_count} old memories for user {user_id}")

        return deleted_count

    except Exception as e:
        logger.error(f"Error cleaning up memories: {e}")
        return 0


async def deduplicate_memories(
    user_id: str, supabase: Client, similarity_threshold: float = 0.95
) -> int:
    """
    Remove duplicate or very similar memories to reduce redundancy.

    Args:
        user_id: UUID of the user
        supabase: Supabase client
        similarity_threshold: Consider memories duplicates if similarity > threshold

    Returns:
        Number of duplicate memories removed
    """
    try:
        # Get all memories for user
        result = supabase.table("memories").select("*").eq("user_id", user_id).execute()

        if not result.data or len(result.data) < 2:
            return 0

        memories = result.data
        to_delete = []

        # Compare memories (simple content-based deduplication)
        seen_content = {}
        for memory in memories:
            content = memory.get("content", "")
            memory_id = memory.get("id")

            if content in seen_content:
                # Duplicate content found
                to_delete.append(memory_id)
            else:
                seen_content[content] = memory_id

        # Delete duplicates
        for memory_id in to_delete:
            supabase.table("memories").delete().eq("id", memory_id).execute()

        logger.info(f"Removed {len(to_delete)} duplicate memories for user {user_id}")
        return len(to_delete)

    except Exception as e:
        logger.error(f"Error deduplicating memories: {e}")
        return 0


# ============================================================================
# Testing and Debugging Helpers
# ============================================================================


async def create_test_memory(
    user_id: str, supabase: Client, test_scenario: str = "login"
) -> bool:
    """
    Create a test memory for development and testing.

    Args:
        user_id: UUID of the user
        supabase: Supabase client
        test_scenario: Type of test memory to create

    Returns:
        True if created successfully
    """
    scenarios = {
        "login": {
            "content": "User successfully logged into the application",
            "metadata": {"action": "login", "url": "https://example.com/login"},
        },
        "form": {
            "content": "User filled out contact form with name and email",
            "metadata": {
                "action": "form_submission",
                "url": "https://example.com/contact",
            },
        },
        "search": {
            "content": "User searched for Python tutorials and clicked first result",
            "metadata": {"action": "search", "query": "python tutorials"},
        },
        "purchase": {
            "content": "User completed checkout and purchased premium subscription",
            "metadata": {"action": "purchase", "amount": 29.99},
        },
    }

    if test_scenario not in scenarios:
        logger.error(f"Unknown test scenario: {test_scenario}")
        return False

    scenario_data = scenarios[test_scenario]

    return await process_memory_background(
        user_id=user_id,
        interaction_summary=scenario_data["content"],
        supabase=supabase,
        metadata=scenario_data["metadata"],
    )
