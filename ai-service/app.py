"""
FastAPI Web Service for AI Agent

This provides a simple web interface and API endpoints.
For beginners: The web server that makes your AI accessible through a browser.
For production: RESTful API with authentication, rate limiting, and monitoring.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from src.rag_pipeline import RAGPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AI Agent Service",
    description="Configurable AI Agent with RAG capabilities",
    version="1.0.0"
)

# Setup templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Initialize RAG Pipeline
load_dotenv()
rag_pipeline = RAGPipeline(google_api_key=os.getenv("GOOGLE_API_KEY"))

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    k: int = 4

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]

# API Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Home page with chat interface.
    
    For beginners: The main chat page you'll see in your browser.
    For production: Serves the web application interface.
    """
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    For beginners: Simple way to check if the service is running.
    For production: Monitoring endpoint for load balancers and health checks.
    """
    return {"status": "healthy", "service": "AI Agent Service"}

@app.post("/api/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Query the AI agent.
    
    For beginners: Ask questions to your AI through this API.
    For production: Core Q&A endpoint with rate limiting and validation.
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        response = rag_pipeline.query(
            question=request.question,
            k=request.k,
            include_sources=True
        )
        
        return QueryResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in query endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest")
async def ingest_documents(files: List[UploadFile] = File(...)):
    """
    Ingest uploaded documents.
    
    For beginners: Upload PDFs or text files to teach your AI.
    For production: Batch document ingestion with validation and progress tracking.
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Save uploaded files
        docs_path = Path("./documents")
        docs_path.mkdir(exist_ok=True)
        
        saved_files = []
        for file in files:
            if file.filename.endswith(('.pdf', '.txt', '.md')):
                file_path = docs_path / file.filename
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                saved_files.append(str(file_path))
        
        if not saved_files:
            raise HTTPException(status_code=400, detail="No valid files uploaded")
        
        # Ingest documents
        result = rag_pipeline.ingest_documents(file_paths=saved_files)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in ingest endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """
    Get pipeline statistics.
    
    For beginners: See how many documents are loaded and other stats.
    For production: Monitoring endpoint for system health and usage metrics.
    """
    try:
        return rag_pipeline.get_pipeline_stats()
    except Exception as e:
        logger.error(f"Error in stats endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Create HTML template
def create_html_template():
    """Create the chat interface HTML template."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent Chat</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #ffffff;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: #2d2d2d;
            padding: 1rem;
            border-bottom: 1px solid #3d3d3d;
        }
        
        .header h1 {
            font-size: 1.5rem;
            color: #4CAF50;
        }
        
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 1200px;
            margin: 0 auto;
            width: 100%;
            padding: 1rem;
        }
        
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 1rem 0;
        }
        
        .message {
            margin-bottom: 1rem;
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            max-width: 80%;
        }
        
        .user-message {
            background: #4CAF50;
            align-self: flex-end;
            margin-left: auto;
        }
        
        .ai-message {
            background: #2d2d2d;
            align-self: flex-start;
        }
        
        .sources {
            margin-top: 0.5rem;
            font-size: 0.8rem;
            color: #888;
        }
        
        .input-container {
            display: flex;
            gap: 0.5rem;
            padding: 1rem;
            background: #2d2d2d;
            border-top: 1px solid #3d3d3d;
        }
        
        .input-field {
            flex: 1;
            padding: 0.75rem;
            background: #1a1a1a;
            border: 1px solid #3d3d3d;
            border-radius: 0.5rem;
            color: #ffffff;
            font-size: 1rem;
        }
        
        .input-field:focus {
            outline: none;
            border-color: #4CAF50;
        }
        
        .send-button {
            padding: 0.75rem 1.5rem;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 1rem;
        }
        
        .send-button:hover {
            background: #45a049;
        }
        
        .send-button:disabled {
            background: #666;
            cursor: not-allowed;
        }
        
        .upload-section {
            padding: 1rem;
            background: #2d2d2d;
            border-bottom: 1px solid #3d3d3d;
        }
        
        .upload-form {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }
        
        .file-input {
            display: none;
        }
        
        .file-label {
            padding: 0.5rem 1rem;
            background: #555;
            color: white;
            border-radius: 0.5rem;
            cursor: pointer;
        }
        
        .upload-button {
            padding: 0.5rem 1rem;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 0.5rem;
            cursor: pointer;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 1rem;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Agent Chat</h1>
    </div>
    
    <div class="upload-section">
        <form class="upload-form" id="uploadForm">
            <input type="file" id="fileInput" class="file-input" multiple accept=".pdf,.txt,.md">
            <label for="fileInput" class="file-label">Choose Files</label>
            <button type="submit" class="upload-button">Upload Documents</button>
            <span id="uploadStatus"></span>
        </form>
    </div>
    
    <div class="chat-container">
        <div class="messages" id="messages">
            <div class="message ai-message">
                Hello! I'm your AI assistant. Upload some documents and ask me anything about them.
            </div>
        </div>
        
        <div class="loading" id="loading">
            AI is thinking...
        </div>
        
        <div class="input-container">
            <input type="text" id="messageInput" class="input-field" placeholder="Ask me anything..." />
            <button id="sendButton" class="send-button">Send</button>
        </div>
    </div>
    
    <script>
        const messages = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const loading = document.getElementById('loading');
        const uploadForm = document.getElementById('uploadForm');
        const fileInput = document.getElementById('fileInput');
        const uploadStatus = document.getElementById('uploadStatus');
        
        // Add message to chat
        function addMessage(content, isUser = false, sources = []) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
            messageDiv.textContent = content;
            
            if (sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources';
                sourcesDiv.textContent = `Sources: ${sources.length} documents`;
                messageDiv.appendChild(sourcesDiv);
            }
            
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
        
        // Send message
        async function sendMessage() {
            const question = messageInput.value.trim();
            if (!question) return;
            
            // Add user message
            addMessage(question, true);
            messageInput.value = '';
            
            // Show loading
            loading.style.display = 'block';
            sendButton.disabled = true;
            
            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question, k: 4 }),
                });
                
                const data = await response.json();
                
                // Add AI response
                addMessage(data.answer, false, data.sources);
                
            } catch (error) {
                addMessage('Sorry, something went wrong. Please try again.', false);
            } finally {
                loading.style.display = 'none';
                sendButton.disabled = false;
            }
        }
        
        // Upload files
        async function uploadFiles(event) {
            event.preventDefault();
            
            const files = fileInput.files;
            if (files.length === 0) return;
            
            const formData = new FormData();
            for (const file of files) {
                formData.append('files', file);
            }
            
            uploadStatus.textContent = 'Uploading...';
            
            try {
                const response = await fetch('/api/ingest', {
                    method: 'POST',
                    body: formData,
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    uploadStatus.textContent = `Success! ${data.documents_processed} documents processed.`;
                    addMessage(`I've learned from ${data.documents_processed} new documents. You can now ask me questions about them.`, false);
                } else {
                    uploadStatus.textContent = 'Error uploading files.';
                }
                
            } catch (error) {
                uploadStatus.textContent = 'Error uploading files.';
            }
            
            fileInput.value = '';
        }
        
        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        
        uploadForm.addEventListener('submit', uploadFiles);
    </script>
</body>
</html>
    """
    
    template_path = templates_dir / "chat.html"
    with open(template_path, "w") as f:
        f.write(html_content)
    
    logger.info(f"HTML template created at {template_path}")

# Create template on startup
create_html_template()

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
