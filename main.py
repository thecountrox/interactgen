"""
FastAPI Backend for Browser Automation Agent
============================================
Handles page analysis, WebSocket chat, and memory logging
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, List
from datetime import datetime
import os
import logging
from contextlib import asynccontextmanager
import dotenv 

dotenv.load_dotenv()

# Configure logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase client
from supabase import create_client, Client

# Conditional LLM/Embedding API import based on USE_LOCAL_LLM
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

if USE_LOCAL_LLM:
    logger.info("🏠 Using LOCAL LLM (Ollama)")
    from ollama_api import (
        generate_embedding,
        call_gemini_with_context,
        generate_chatbot_response,
        check_ollama_status
    )
    # Check Ollama status on startup
    ollama_status = check_ollama_status()
    if not ollama_status['available']:
        logger.error(f"❌ Ollama not available: {ollama_status.get('error')}")
        logger.error("   Install: curl -fsSL https://ollama.com/install.sh | sh")
        logger.error(f"   Pull models: ollama pull {os.getenv('OLLAMA_LLM_MODEL', 'llama3.2:3b-instruct-q4_K_M')}")
    else:
        logger.info(f"✓ Ollama connected: {ollama_status['host']}")
        logger.info(f"  Available models: {', '.join(ollama_status['models'][:3])}")
else:
    logger.info("☁️  Using CLOUD LLM (Gemini API)")
    from gemini_api import (
        generate_embedding,
        call_gemini_with_context,
        generate_chatbot_response
    )

# Rate Limiter (only used for Gemini API)
from rate_limiter import get_usage_stats

# Judge Engine
from judge_engine import evaluate_page, store_interaction_memory

# Tertiary Chat Layer (Proactive Tutor)
from tertiary_chat import analyze_and_nudge, handle_chat_query

# Memory Worker (Background Learning)
from memory_worker import process_memory_background, process_interaction_memory

# ============================================================================
# Configuration & Initialization
# ============================================================================

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Global Supabase client
supabase: Optional[Client] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events"""
    # Startup
    global supabase
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        raise ValueError("Missing Supabase configuration")
    
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set - embedding generation will fail")
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✓ Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Initialize FastAPI with lifespan
app = FastAPI(
    title="InteractGen Browser Automation Agent",
    description="3-Layer Architecture: Reading → Judge → Actions",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# CORS Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Pydantic Models
# ============================================================================

class PageContext(BaseModel):
    """Context data from the browser for analysis"""
    url: str = Field(..., description="The URL of the page being analyzed")
    html_content: str = Field(..., description="The HTML content of the page")
    user_id: UUID4 = Field(..., description="UUID of the user making the request")
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional context metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "html_content": "<html><body>Example content</body></html>",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "metadata": {
                    "viewport": "desktop",
                    "timestamp": "2025-12-12T10:30:00Z"
                }
            }
        }


class AnalysisResponse(BaseModel):
    """Response from the analyze endpoint"""
    success: bool
    message: str
    analysis_id: Optional[str] = None
    suggestions: Optional[List[str]] = None
    actions: Optional[List[Dict]] = None


class ChatMessage(BaseModel):
    """WebSocket chat message structure"""
    user_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class ConnectionManager:
    """Manages active WebSocket connections for the helpful chatbot"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Remove a disconnected client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json({
                    "type": "tip",
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients"""
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json({
                    "type": "broadcast",
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)


# Global connection manager instance
connection_manager = ConnectionManager()

# ============================================================================
# Background Tasks
# ============================================================================

async def log_interaction_for_memory(
    user_id: str,
    url: str,
    html_content: str,
    metadata: Optional[Dict] = None
):
    """
    Background task to log the interaction for future memory embedding.
    Uses the memory_worker module to process and store with embeddings.
    """
    try:
        logger.info(f"📝 Processing interaction for memory storage: {url}")
        
        # Extract page title if possible
        from bs4 import BeautifulSoup
        page_title = None
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            page_title = soup.title.string if soup.title else None
        except:
            pass
        
        # Create a concise summary
        html_summary = html_content[:200] if html_content else ""
        
        # Use the memory worker to process and store
        success = await process_interaction_memory(
            user_id=user_id,
            url=url,
            action="visited page",
            supabase=supabase,
            page_title=page_title,
            html_summary=html_summary,
            metadata=metadata
        )
        
        if success:
            logger.info(f"✅ Memory stored successfully for {url}")
        else:
            logger.warning(f"⚠️ Failed to store memory (may be quota limited)")
        
    except Exception as e:
        logger.error(f"Error logging interaction: {e}")


# ============================================================================
# Judge Layer Placeholder
# ============================================================================

async def judge_page_context(context: PageContext) -> Dict:
    """
    Judge Layer: Analyzes page context using LLM + RAG.
    
    Process:
    1. Get user profile for personalization
    2. Query vector memories for relevant context (RAG)
    3. Send to Gemini LLM for intelligent analysis
    4. Return structured decisions (what to hide, highlight, suggest)
    """
    
    try:
        # Get user profile and context
        user_profile = supabase.table("profiles").select("*").eq("id", str(context.user_id)).execute()
        
        if not user_profile.data:
            logger.warning(f"No profile found for user {context.user_id}")
            user_context = {"technical_level": "intermediate"}
        else:
            user_context = user_profile.data[0]
        
        # Call the Judge Engine with RAG + LLM
        logger.info(f"🧠 Calling Judge Engine for {context.url}")
        
        judge_result = await evaluate_page(
            html=context.html_content,
            user_id=str(context.user_id),
            supabase=supabase,
            url=context.url,
            user_context=user_context
        )
        
        # Transform judge result into action format
        actions = []
        
        # Add hide actions
        for selector in judge_result.get("hidden_selectors", []):
            actions.append({
                "type": "hide",
                "selector": selector,
                "reason": "Reducing clutter based on your preferences"
            })
        
        # Add highlight actions
        for selector in judge_result.get("highlight_selectors", []):
            actions.append({
                "type": "highlight",
                "selector": selector,
                "reason": "Key element for your attention"
            })
        
        # Add suggested action if present
        suggestions = [judge_result.get("summary", "Page analyzed")]
        if judge_result.get("suggested_action"):
            suggestions.append(f"💡 {judge_result['suggested_action']}")
            actions.append({
                "type": "suggestion",
                "message": judge_result["suggested_action"]
            })
        
        return {
            "suggestions": suggestions,
            "actions": actions,
            "judge_result": judge_result  # Include raw judge output for debugging
        }
        
    except Exception as e:
        logger.error(f"Error in judge layer: {e}", exc_info=True)
        return {
            "suggestions": ["Error analyzing page - using fallback mode"],
            "actions": [
                {"type": "highlight", "selector": "button[type='submit']"},
                {"type": "highlight", "selector": ".primary-button"}
            ]
        }


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "InteractGen Browser Automation Agent",
        "version": "1.0.0",
        "layers": {
            "reading": "BeautifulSoup",
            "judge": "LLM + RAG (Supabase pgvector)",
            "actions": "Playwright"
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    supabase_status = "connected" if supabase else "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "supabase": supabase_status,
            "websocket_connections": len(connection_manager.active_connections)
        }
    }


@app.get("/api/rate-limit-status")
async def rate_limit_status():
    """Get current rate limit usage statistics"""
    stats = get_usage_stats()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "rate_limiting": stats
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_page(context: PageContext, background_tasks: BackgroundTasks):
    """
    Analyze page context using the Judge layer.
    
    - Accepts page context (URL, HTML, user ID)
    - Calls Judge layer for analysis
    - Logs interaction in background for future memory embedding
    - Returns suggestions and actions for the Actions layer
    """
    try:
        logger.info(f"📊 Analyzing page for user {context.user_id}: {context.url}")
        
        # Add background task to log interaction for memory
        background_tasks.add_task(
            log_interaction_for_memory,
            str(context.user_id),
            context.url,
            context.html_content,
            context.metadata
        )
        
        # Call the Judge layer
        analysis_result = await judge_page_context(context)
        
        # Get user profile for tertiary chat
        user_id_str = str(context.user_id)
        try:
            user_profile = supabase.table("profiles").select("*").eq("id", user_id_str).execute()
            user_prof_data = user_profile.data[0] if user_profile.data else {
                "technical_level": "intermediate",
                "username": "user"
            }
        except:
            user_prof_data = {"technical_level": "intermediate", "username": "user"}
        
        # Tertiary Layer: Send proactive nudge if user is connected via WebSocket
        if user_id_str in connection_manager.active_connections:
            logger.info("🎯 Generating proactive nudge for connected user...")
            
            # Run tertiary chat analysis in background (non-blocking)
            background_tasks.add_task(
                analyze_and_nudge,
                connection_manager,
                user_id_str,
                context.html_content,
                user_prof_data,
                context.url
            )
        
        return AnalysisResponse(
            success=True,
            message="Page analyzed successfully",
            analysis_id=f"analysis_{datetime.utcnow().timestamp()}",
            suggestions=analysis_result.get("suggestions"),
            actions=analysis_result.get("actions")
        )
        
    except Exception as e:
        logger.error(f"Error analyzing page: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.websocket("/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for the helpful chatbot.
    
    - Maintains persistent connection with browser extension
    - Sends context-aware tips and suggestions
    - Receives user queries and feedback
    """
    await connection_manager.connect(client_id, websocket)
    
    try:
        # Send welcome message
        await connection_manager.send_personal_message(
            "👋 Connected! I'm here to help you navigate and automate.",
            client_id
        )
        
        # Listen for messages
        while True:
            data = await websocket.receive_json()
            logger.info(f"📨 Message from {client_id}: {data}")
            
            message_type = data.get("type", "message")
            
            if message_type == "query":
                # Handle user query using tertiary chat layer
                user_message = data.get("message", "")
                
                # Get user profile
                try:
                    user_profile = supabase.table("profiles").select("*").eq("id", client_id).execute()
                    user_prof = user_profile.data[0] if user_profile.data else {
                        "username": client_id,
                        "technical_level": "intermediate"
                    }
                except:
                    user_prof = {"username": client_id, "technical_level": "intermediate"}
                
                # Get page context if available
                page_context = data.get("page_context")
                
                # Generate intelligent response using tertiary chat
                logger.info(f"💬 Processing chat query from {client_id}: {user_message}")
                response = await handle_chat_query(
                    user_message=user_message,
                    user_profile=user_prof,
                    page_context=page_context
                )
                
                await connection_manager.send_personal_message(
                    f"🤖 {response}",
                    client_id
                )
                
            elif message_type == "feedback":
                # Handle user feedback
                logger.info(f"Feedback from {client_id}: {data.get('feedback')}")
                await connection_manager.send_personal_message(
                    "✓ Thanks for your feedback!",
                    client_id
                )
            
            else:
                # Echo back for other message types
                await connection_manager.send_personal_message(
                    f"Echo: {data}",
                    client_id
                )
    
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        connection_manager.disconnect(client_id)


@app.post("/broadcast")
async def broadcast_message(message: str):
    """
    Admin endpoint to broadcast a message to all connected clients.
    Useful for system-wide notifications.
    """
    await connection_manager.broadcast(message)
    return {
        "success": True,
        "message": "Broadcast sent",
        "recipients": len(connection_manager.active_connections)
    }


# ============================================================================
# Development & Testing Endpoints
# ============================================================================

@app.get("/connections")
async def get_active_connections():
    """Get list of active WebSocket connections (dev/debug only)"""
    return {
        "active_connections": list(connection_manager.active_connections.keys()),
        "count": len(connection_manager.active_connections)
    }


@app.get("/memories/{user_id}")
async def get_user_memories(user_id: str, limit: int = 10):
    """
    Get recent memories for a user.
    
    Args:
        user_id: UUID of the user
        limit: Maximum number of memories to return
    """
    try:
        from memory_worker import get_user_memory_stats
        
        stats = await get_user_memory_stats(user_id, supabase)
        
        # Also get recent memories
        result = supabase.table("memories").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        
        return {
            "user_id": user_id,
            "stats": stats,
            "recent_memories": result.data if result.data else []
        }
        
    except Exception as e:
        logger.error(f"Error fetching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memories/search")
async def search_memories_endpoint(user_id: str, query: str, top_k: int = 5):
    """
    Search a user's memories using semantic similarity.
    
    Args:
        user_id: UUID of the user
        query: Search query (natural language)
        top_k: Number of results to return
    """
    try:
        from memory_worker import search_user_memories
        
        memories = await search_user_memories(
            user_id=user_id,
            query=query,
            supabase=supabase,
            top_k=top_k
        )
        
        return {
            "query": query,
            "user_id": user_id,
            "results": memories,
            "count": len(memories)
        }
        
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memories/create-test")
async def create_test_memory_endpoint(user_id: str, scenario: str = "login"):
    """
    Create a test memory for development and testing.
    
    Args:
        user_id: UUID of the user
        scenario: Type of test (login, form, search, purchase)
    """
    try:
        from memory_worker import create_test_memory
        
        success = await create_test_memory(
            user_id=user_id,
            supabase=supabase,
            test_scenario=scenario
        )
        
        return {
            "success": success,
            "user_id": user_id,
            "scenario": scenario,
            "message": "Test memory created" if success else "Failed to create test memory"
        }
        
    except Exception as e:
        logger.error(f"Error creating test memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))
async def get_active_connections():
    """Get list of active WebSocket connections (dev/debug only)"""
    return {
        "active_connections": list(connection_manager.active_connections.keys()),
        "count": len(connection_manager.active_connections)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
