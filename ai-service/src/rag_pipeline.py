"""
Complete RAG Pipeline using Google Gemini

This module orchestrates the entire RAG process from document loading to query answering.
For beginners: The complete brain of your AI system - reads documents, thinks, and answers.
For production: Optimized pipeline with caching, error handling, and performance monitoring.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from src.document_loader import DocumentLoader
from src.text_chunker import TextChunker
from src.vector_store_gemini import VectorStoreGemini
from src.free_tier_manager import FreeTierManager

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Complete RAG pipeline for document Q&A.
    
    For beginners: Loads documents, finds relevant info, and answers questions.
    For production: Scalable pipeline with caching, monitoring, and error recovery.
    """
    
    def __init__(self, 
                 docs_path: str = "./documents",
                 vector_db_path: str = "./vector_db",
                 google_api_key: str = None):
        """
        Initialize the RAG pipeline.
        
        Args:
            docs_path: Path to documents directory
            vector_db_path: Path to vector database
            google_api_key: Google Gemini API key
        """
        load_dotenv()
        
        # Initialize components
        self.document_loader = DocumentLoader(docs_path)
        self.text_chunker = TextChunker()
        self.vector_store = VectorStoreGemini(
            vector_db_path=vector_db_path,
            google_api_key=google_api_key or os.getenv("GOOGLE_API_KEY")
        )
        
        # Initialize free tier manager
        self.free_tier_manager = FreeTierManager()
        
        # Load existing vector store if available
        self.vector_store.load_vector_store()
        
        # Create prompt template
        self._create_prompt_template()
    
    def _create_prompt_template(self):
        """
        Create a prompt template for Q&A.
        
        For beginners: Template for how the AI should answer questions.
        For production: Optimized prompt for factual accuracy and citation.
        """
        template = """
        You are a helpful AI assistant. Use the following context to answer the user's question.
        If you don't know the answer from the context, say "I don't have enough information to answer this."
        Always cite your sources using the document information provided.
        
        Context:
        {context}
        
        Question:
        {question}
        
        Answer:
        """
        
        self.qa_prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def ingest_documents(self, 
                        file_paths: List[str] = None,
                        chunk_strategy: str = "general") -> Dict[str, Any]:
        """
        Ingest documents into the RAG pipeline.
        
        For beginners: Adds new documents to the AI's knowledge base.
        For production: Batch processing with progress tracking and error handling.
        
        Args:
            file_paths: Specific files to process (None for all)
            chunk_strategy: Strategy for text chunking
            
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info("Starting document ingestion")
        
        try:
            # Load documents
            if file_paths:
                documents = []
                for file_path in file_paths:
                    docs = self.document_loader.load_single_document(file_path)
                    documents.extend(docs)
            else:
                documents = self.document_loader.load_all_documents()
            
            if not documents:
                return {"status": "No documents found", "documents_processed": 0}
            
            # Chunk documents
            chunked_docs = self.text_chunker.chunk_documents(documents, strategy=chunk_strategy)
            
            # Add to vector store
            self.vector_store.add_documents(chunked_docs)
            
            # Get statistics
            stats = {
                "status": "success",
                "documents_processed": len(documents),
                "chunks_created": len(chunked_docs),
                "chunk_strategy": chunk_strategy,
                "vector_store_stats": self.vector_store.get_stats()
            }
            
            logger.info(f"Ingestion complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error during ingestion: {e}")
            return {"status": "error", "error": str(e)}
    
    def query(self, 
              question: str,
              k: int = 4,
              include_sources: bool = True) -> Dict[str, Any]:
        """
        Query the RAG pipeline.
        
        For beginners: Ask a question and get an answer from your documents.
        For production: Optimized query with relevance scoring and source attribution.
        
        Args:
            question: User's question
            k: Number of documents to retrieve
            include_sources: Whether to include source documents
            
        Returns:
            Dictionary with answer and metadata
        """
        logger.info(f"Processing query: {question[:50]}...")
        
        # Check free tier limits before making API call
        model = "gemini-2.5-flash"  # Using the free tier model
        can_make_request, reason = self.free_tier_manager.can_make_request(model)
        
        if not can_make_request:
            wait_time = self.free_tier_manager.get_wait_time(model)
            usage_stats = self.free_tier_manager.get_usage_stats()
            daily_usage = usage_stats.get('daily', {}).get(model, {})
            
            # Create detailed user-friendly message
            user_message = f"""=== QUOTA LIMIT REACHED ===

Daily Limit: {daily_usage.get('limit', 20)} requests
Used: {daily_usage.get('used', 0)} requests  
Remaining: {daily_usage.get('remaining', 0)} requests

{reason}

=== YOUR OPTIONS ===
1. Wait for quota reset (tomorrow)
2. Use local demo: python local_chat.py
3. Check status: python quota_wait_time.py

=== RECOMMENDATION ===
Use 'python local_chat.py' for immediate testing without API limits!
=============================="""
            
            return {
                "answer": user_message,
                "sources": [],
                "metadata": {
                    "error": "RATE_LIMIT_EXCEEDED",
                    "wait_time_seconds": wait_time,
                    "usage_stats": usage_stats,
                    "quota_exceeded": True
                }
            }
        
        try:
            # Retrieve relevant documents
            relevant_docs = self.vector_store.similarity_search(
                query=question,
                k=k,
                score_threshold=0.6  # Adjust based on your needs
            )
            
            if not relevant_docs:
                return {
                    "answer": "I don't have enough information to answer this question.",
                    "sources": [],
                    "metadata": {"retrieved_docs": 0, "question": question}
                }
            
            # Build context
            context = "\n\n".join(doc.page_content for doc in relevant_docs)
            
            # Generate answer using Gemini
            prompt = self.qa_prompt.format(context=context, question=question)
            
            try:
                response = self.vector_store.chat_model.invoke(prompt)
            except Exception as e:
                # Check if it's a quota exceeded error
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
                    logger.error(f"API quota exceeded: {e}")
                    
                    # Return the same quota exceeded message
                    usage_stats = self.free_tier_manager.get_usage_stats()
                    daily_usage = usage_stats.get('daily', {}).get(model, {})
                    
                    user_message = f"""=== QUOTA LIMIT REACHED ===

Daily Limit: {daily_usage.get('limit', 20)} requests
Used: {daily_usage.get('used', 0)} requests  
Remaining: {daily_usage.get('remaining', 0)} requests

API quota exceeded. Please try again tomorrow.

=== YOUR OPTIONS ===
1. Wait for quota reset (tomorrow)
2. Use local demo: python local_chat.py
3. Check status: python quota_wait_time.py

=== RECOMMENDATION ===
Use 'python local_chat.py' for immediate testing without API limits!
=============================="""
                    
                    return {
                        "answer": user_message,
                        "sources": [],
                        "metadata": {
                            "error": "RATE_LIMIT_EXCEEDED",
                            "quota_exceeded": True,
                            "usage_stats": usage_stats
                        }
                    }
                else:
                    # Re-raise other exceptions
                    raise e
            
            # Record successful API request for usage tracking
            self.free_tier_manager.record_request(model)
            
            # Prepare result
            result = {
                "answer": response.content,
                "question": question,
                "metadata": {
                    "retrieved_docs": len(relevant_docs),
                    "context_length": len(context),
                    "model": "gemini-2.5-flash"
                }
            }
            
            # Add sources if requested
            if include_sources:
                sources = []
                for doc in relevant_docs:
                    sources.append({
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata,
                        "similarity_score": doc.metadata.get('similarity_score', 0)
                    })
                result["sources"] = sources
            
            logger.info(f"Query processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "answer": f"An error occurred while processing your question: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e)}
            }
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get complete pipeline statistics.
        
        Returns:
            Dictionary with pipeline information
        """
        return {
            "document_loader": self.document_loader.get_document_info(),
            "vector_store": self.vector_store.get_stats(),
            "chat_model": {
                "model": "gemini-2.5-flash",
                "provider": "Google"
            },
            "free_tier_usage": self.free_tier_manager.get_usage_stats()
        }

# Example usage
if __name__ == "__main__":
    # Test the complete RAG pipeline
    print("=== RAG Pipeline Test ===")
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in your .env file")
        exit(1)
    
    # Create pipeline
    pipeline = RAGPipeline(google_api_key=api_key)
    
    # Show stats
    stats = pipeline.get_pipeline_stats()
    print(f"Pipeline stats: {stats}")
    
    # Ingest documents if needed
    if stats["vector_store"].get("total_vectors", 0) == 0:
        print("No documents in vector store. Ingesting...")
        result = pipeline.ingest_documents()
        print(f"Ingestion result: {result}")
    
    # Test query
    print("\nTesting query...")
    response = pipeline.query("What information do you have about real estate?")
    print(f"Answer: {response['answer']}")
    print(f"Sources: {len(response.get('sources', []))} documents used")
