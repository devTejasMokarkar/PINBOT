"""
Complete WhatsApp Server for PinBot

Run this server to connect your AI agent to WhatsApp.
"""

import os
import logging
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import uvicorn

# Import our WhatsApp integration
try:
    from src.agent_with_persona import AgentWithPersona
    from whatsapp_integration import create_whatsapp_app
except ImportError:
    from agent_with_persona import AgentWithPersona
    from whatsapp_integration import create_whatsapp_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Initialize AI Agent
agent = AgentWithPersona(google_api_key=os.getenv("GOOGLE_API_KEY"))
agent.set_persona("Real Estate Agent")

# Create FastAPI app with WhatsApp endpoints
app = create_whatsapp_app(agent)

# Add health check endpoint
@app.get("/")
async def root():
    return {
        "service": "PinBot WhatsApp Integration",
        "status": "running",
        "persona": agent.current_persona['name'] if agent.current_persona else None,
        "endpoints": {
            "webhook": "/webhook",
            "send_test": "/send-test",
            "status": "/status",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Start server
if __name__ == "__main__":
    print("""
    ========================================
    PinBot WhatsApp Server Starting...
    ========================================
    
    Server will run on: http://localhost:8000
    
    Endpoints:
    - GET  /           : Service info
    - GET  /health     : Health check
    - GET  /webhook    : WhatsApp webhook verification
    - POST /webhook    : Receive WhatsApp messages
    - POST /send-test  : Send test message
    - GET  /status     : Integration status
    
    Before starting:
    1. Set up WhatsApp Business API (see WHATSAPP_SETUP.md)
    2. Update your .env file with WhatsApp credentials
    3. Your webhook URL: http://localhost:8000/webhook
    
    ========================================
    """)
    
    uvicorn.run(
        "whatsapp_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
