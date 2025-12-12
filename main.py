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


# Supabase client
from supabase import create_client, Client

# Gemini API integration
from gemini_api import (
    generate_embedding,
    call_gemini_with_context,
    generate_chatbot_response
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    This will be used by the Judge layer to build context over time.
    """
    try:
        # Create a condensed summary for storage
        content_summary = f"User visited: {url}"
        
        # Prepare interaction log
        interaction_data = {
            "user_id": user_id,
            "url": url,
            "content_length": len(html_content),
            "metadata": metadata or {},
            "logged_at": datetime.utcnow().isoformat()
        }
        
        # TODO: In production, this would:
        # 1. Generate embedding via Gemini API
        # 2. Store in memories table with embedding
        # For now, we'll store a basic interaction log
        
        # Insert into a generic interaction_logs table (or prepare for embedding)
        logger.info(f"📝 Logged interaction for user {user_id} on {url}")
        logger.debug(f"Interaction data: {interaction_data}")
        
        # Note: Actual embedding generation would happen here:
        # embedding = await generate_embedding(content_summary)
        # supabase.table("memories").insert({
        #     "user_id": user_id,
        #     "content": content_summary,
        #     "embedding": embedding,
        #     "metadata": interaction_data
        # }).execute()
        
    except Exception as e:
        logger.error(f"Error logging interaction: {e}")


# ============================================================================
# Judge Layer Placeholder
# ============================================================================

async def judge_page_context(context: PageContext) -> Dict:
    """
    Placeholder for the Judge Layer logic.
    This will use LLMs + RAG to decide UI modifications and actions.
    
    TODO: Implement:
    1. Query Supabase for relevant memories using vector similarity
    2. Build context from user profile + memories
    3. Send to LLM (Gemini) for analysis
    4. Return suggested actions and UI modifications
    """
    
    try:
        # Get user profile and context
        user_profile = supabase.table("profiles").select("*").eq("id", str(context.user_id)).execute()
        
        if not user_profile.data:
            logger.warning(f"No profile found for user {context.user_id}")
            user_context = {"technical_level": "intermediate"}
        else:
            user_context = user_profile.data[0]
        
        # TODO: Query vector memories for relevant context
        # relevant_memories = await search_similar_memories(context, user_id)
        
        # TODO: Call Gemini API with context
        # llm_response = await call_gemini_with_context(context, user_context, relevant_memories)
        
        # Placeholder response
        return {
            "suggestions": [
                f"Analyzing page: {context.url}",
                f"User technical level: {user_context.get('technical_level', 'unknown')}",
                "Ready to provide context-aware assistance"
            ],
            "actions": [
                {"type": "highlight", "selector": "button.primary"},
                {"type": "tooltip", "message": "This button submits the form"}
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in judge layer: {e}")
        return {
            "suggestions": ["Error analyzing page"],
            "actions": []
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
        
        # Call the Judge layer (placeholder for now)
        analysis_result = await judge_page_context(context)
        
        # Send helpful tip via WebSocket if user is connected
        user_id_str = str(context.user_id)
        if user_id_str in connection_manager.active_connections:
            await connection_manager.send_personal_message(
                f"💡 Tip: I'm analyzing {context.url} for you!",
                user_id_str
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
                # Handle user query
                user_message = data.get("message", "")
                # TODO: Process query with LLM and send intelligent response
                response = f"🤖 I received your query: '{user_message}'. Processing..."
                await connection_manager.send_personal_message(response, client_id)
                
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
