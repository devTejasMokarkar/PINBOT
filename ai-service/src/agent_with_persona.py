"""
AI Agent with Persona Support

This extends the RAG pipeline with configurable personas.
For beginners: Give your AI a personality and specific role.
For production: Multi-tenant agents with different personas per use case.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

from src.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

class AgentWithPersona:
    """
    AI Agent with configurable persona.
    
    For beginners: AI that acts like a specific character (realtor, assistant, etc.).
    For production: Scalable agent system with persona management.
    """
    
    def __init__(self, 
                 persona_config_path: str = "./personas",
                 vector_db_path: str = "./vector_db",
                 uploads_path: str = "./Uploads",
                 google_api_key: str = None):
        """
        Initialize agent with persona support.
        
        Args:
            persona_config_path: Path to persona configuration files
            vector_db_path: Path to vector database
            uploads_path: Path for manual document uploads
            google_api_key: Google Gemini API key
        """
        load_dotenv()
        
        # Paths
        self.persona_path = Path(persona_config_path)
        self.uploads_path = Path(uploads_path)
        self.vector_db_path = Path(vector_db_path)
        
        # Create directories
        self.persona_path.mkdir(exist_ok=True)
        self.uploads_path.mkdir(exist_ok=True)
        self.vector_db_path.mkdir(exist_ok=True)
        
        # Initialize RAG pipeline
        self.rag_pipeline = RAGPipeline(
            docs_path=str(self.uploads_path),
            vector_db_path=str(self.vector_db_path),
            google_api_key=google_api_key or os.getenv("GOOGLE_API_KEY")
        )
        
        # Load personas
        self.personas = self._load_personas()
        self.current_persona = None
        
        logger.info(f"Agent initialized with {len(self.personas)} personas")
    
    def _load_personas(self) -> Dict[str, Dict]:
        """
        Load persona configurations from JSON files.
        
        For beginners: Different AI personalities stored as JSON.
        For production: Persona management system with templates.
        
        Returns:
            Dictionary of personas
        """
        personas = {}
        
        # Create default personas if they don't exist
        self._create_default_personas()
        
        # Load all persona files
        for persona_file in self.persona_path.glob("*.json"):
            try:
                with open(persona_file, 'r') as f:
                    persona = json.load(f)
                    personas[persona['name']] = persona
                    logger.info(f"Loaded persona: {persona['name']}")
            except Exception as e:
                logger.error(f"Error loading persona {persona_file}: {e}")
        
        return personas
    
    def _create_default_personas(self):
        """Create default persona configurations."""
        default_personas = {
            "real_estate_agent": {
                "name": "Real Estate Agent",
                "description": "A helpful real estate agent",
                "persona": "You are a professional real estate agent named 'PinBot'. You are knowledgeable about properties, pricing, and locations. You always provide helpful, accurate information about real estate. You are friendly but professional.",
                "welcome_message": "Hello! I'm PinBot, your real estate assistant. How can I help you find your dream property today?",
                "capabilities": ["property_qa", "lead_capture", "schedule_viewing"],
                "response_style": "professional yet friendly"
            },
            "general_assistant": {
                "name": "General Assistant",
                "description": "A helpful AI assistant",
                "persona": "You are a helpful AI assistant. You provide accurate, concise answers based on the available information. You are polite and professional.",
                "welcome_message": "Hello! I'm your AI assistant. How can I help you today?",
                "capabilities": ["general_qa", "information_retrieval"],
                "response_style": "helpful and concise"
            },
            "customer_support": {
                "name": "Customer Support",
                "description": "Customer service representative",
                "persona": "You are a customer service representative. You are empathetic, patient, and focused on solving customer problems. Always acknowledge concerns and provide solutions.",
                "welcome_message": "Welcome to customer support! I'm here to help you. What can I assist you with today?",
                "capabilities": ["problem_solving", "information_providing", "escalation"],
                "response_style": "empathetic and solution-oriented"
            }
        }
        
        # Save personas if they don't exist
        for name, persona in default_personas.items():
            persona_file = self.persona_path / f"{name}.json"
            if not persona_file.exists():
                with open(persona_file, 'w') as f:
                    json.dump(persona, f, indent=2)
                logger.info(f"Created default persona: {name}")
    
    def set_persona(self, persona_name: str) -> bool:
        """
        Set the active persona for the agent.
        
        Args:
            persona_name: Name of persona to activate
            
        Returns:
            True if successful, False otherwise
        """
        if persona_name in self.personas:
            self.current_persona = self.personas[persona_name]
            self._update_prompt_template()
            logger.info(f"Persona set to: {persona_name}")
            return True
        else:
            logger.error(f"Persona not found: {persona_name}")
            return False
    
    def _update_prompt_template(self):
        """Update the RAG prompt template based on current persona."""
        if not self.current_persona:
            return
        
        persona_text = self.current_persona.get('persona', '')
        
        template = f"""
        {persona_text}
        
        Use the following context to answer the user's question. If you don't know the answer from the context, say "I don't have enough information to answer this."
        Always cite your sources using the document information provided.
        
        Context:
        {{context}}
        
        Question:
        {{question}}
        
        Answer:
        """
        
        self.rag_pipeline.qa_prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def get_welcome_message(self) -> str:
        """
        Get the welcome message for current persona.
        
        Returns:
            Welcome message string
        """
        if self.current_persona:
            return self.current_persona.get('welcome_message', 'Hello! How can I help you?')
        return 'Hello! How can I help you?'
    
    def ingest_from_uploads(self) -> Dict[str, Any]:
        """
        Ingest documents from the Uploads folder.
        
        For beginners: Automatically learn from files you drop in Uploads folder.
        For production: Watch folder for new documents and auto-ingest.
        
        Returns:
            Ingestion statistics
        """
        logger.info("Ingesting documents from Uploads folder")
        
        # Check if Uploads folder has files
        files = list(self.uploads_path.glob("*"))
        if not files:
            return {"status": "no_files", "message": "No files in Uploads folder"}
        
        # Ingest all documents
        result = self.rag_pipeline.ingest_documents()
        
        return result
    
    def query_with_persona(self, 
                          question: str,
                          persona_name: str = None,
                          k: int = 4) -> Dict[str, Any]:
        """
        Query with persona-specific behavior.
        
        Args:
            question: User's question
            persona_name: Persona to use (optional, uses current if None)
            k: Number of documents to retrieve
            
        Returns:
            Response with persona-specific formatting
        """
        # Set persona if specified
        if persona_name and persona_name != self.current_persona.get('name', ''):
            if not self.set_persona(persona_name):
                return {"error": f"Persona '{persona_name}' not found"}
        
        # Get response from RAG pipeline
        response = self.rag_pipeline.query(question, k=k, include_sources=True)
        
        # Add persona metadata
        if self.current_persona:
            response['persona'] = {
                'name': self.current_persona['name'],
                'response_style': self.current_persona.get('response_style', 'neutral')
            }
        
        return response
    
    def get_available_personas(self) -> Dict[str, Dict]:
        """
        Get list of available personas.
        
        Returns:
            Dictionary of available personas
        """
        return {
            name: {
                'name': persona['name'],
                'description': persona['description'],
                'capabilities': persona.get('capabilities', [])
            }
            for name, persona in self.personas.items()
        }
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """
        Get complete agent statistics.
        
        Returns:
            Dictionary with agent information
        """
        return {
            'current_persona': self.current_persona['name'] if self.current_persona else None,
            'available_personas': list(self.personas.keys()),
            'uploads_folder': str(self.uploads_path),
            'vector_db_path': str(self.vector_db_path),
            'rag_pipeline_stats': self.rag_pipeline.get_pipeline_stats()
        }

# Example usage
if __name__ == "__main__":
    # Test the agent with persona
    print("=== Agent with Persona Test ===")
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in your .env file")
        exit(1)
    
    # Create agent
    agent = AgentWithPersona(google_api_key=api_key)
    
    # Show available personas
    personas = agent.get_available_personas()
    print(f"Available personas: {list(personas.keys())}")
    
    # Set real estate persona
    agent.set_persona("real_estate_agent")
    print(f"Welcome message: {agent.get_welcome_message()}")
    
    # Ingest from uploads
    result = agent.ingest_from_uploads()
    print(f"Ingestion result: {result}")
    
    # Test query
    print("\nTesting query with persona...")
    response = agent.query_with_persona("What properties do you have available?")
    print(f"Response: {response.get('answer', 'No answer')}")
    print(f"Persona: {response.get('persona', {}).get('name', 'No persona')}")
