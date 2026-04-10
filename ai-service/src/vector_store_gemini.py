"""
Vector Store Service using FAISS with Google Gemini

This module handles storing and retrieving document embeddings using Gemini.
For beginners: Think of this as a smart library powered by Google's AI.
For production: Free-tier optimized vector similarity search with Gemini embeddings.
"""

import os
import pickle
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import numpy as np
import faiss
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)

class VectorStoreGemini:
    """
    Manages FAISS vector store using Google Gemini embeddings.
    
    For beginners: Stores document "fingerprints" using Google's AI for fast search.
    For production: Cost-effective vector store with free Gemini embeddings.
    """
    
    def __init__(self, 
                 vector_db_path: str = "./vector_db",
                 google_api_key: str = None):
        """
        Initialize the vector store service.
        
        Args:
            vector_db_path: Path to store FAISS index
            google_api_key: Google Gemini API key
        """
        self.vector_db_path = Path(vector_db_path)
        self.vector_db_path.mkdir(exist_ok=True)
        
        # Initialize Gemini embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=google_api_key,
            model="models/gemini-embedding-001"  # Correct model name from API
        )
        
        # Initialize chat model for later use
        self.chat_model = ChatGoogleGenerativeAI(
            google_api_key=google_api_key,
            model="gemini-2.5-flash",  # Available model with 20 req/day limit
            temperature=0.1  # More factual responses
        )
        
        self.vector_store = None
        self.index_path = self.vector_db_path / "index.faiss"
        self.docs_path = self.vector_db_path / "documents.pkl"
        
    def create_vector_store(self, documents: List[Document]) -> FAISS:
        """
        Create a new vector store from documents using Gemini embeddings.
        
        For beginners: Creates a searchable index using Google's AI.
        For production: Optimized for Gemini's embedding dimensions (768).
        
        Args:
            documents: List of chunked documents
            
        Returns:
            FAISS vector store
        """
        if not documents:
            raise ValueError("No documents provided for vector store creation")
        
        logger.info(f"Creating vector store from {len(documents)} documents using Gemini")
        
        # Create FAISS index with Gemini embeddings
        self.vector_store = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )
        
        # Save the index
        self._save_vector_store()
        
        logger.info(f"Vector store created with {len(documents)} documents")
        return self.vector_store
    
    def load_vector_store(self) -> Optional[FAISS]:
        """
        Load existing vector store from disk.
        
        Returns:
            FAISS vector store or None if not found
        """
        if not self.index_path.exists() or not self.docs_path.exists():
            logger.info("No existing vector store found")
            return None
        
        try:
            # Load FAISS index
            self.vector_store = FAISS.load_local(
                folder_path=str(self.vector_db_path),
                embeddings=self.embeddings
            )
            
            logger.info(f"Loaded vector store from {self.vector_db_path}")
            return self.vector_store
            
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return None
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add new documents to existing vector store.
        
        Args:
            documents: New documents to add
        """
        if not self.vector_store:
            # Create new store if none exists
            self.create_vector_store(documents)
        else:
            # Add to existing store
            self.vector_store.add_documents(documents)
            self._save_vector_store()
        
        logger.info(f"Added {len(documents)} documents to vector store")
    
    def similarity_search(self, 
                         query: str, 
                         k: int = 4,
                         score_threshold: float = 0.7) -> List[Document]:
        """
        Search for similar documents using Gemini embeddings.
        
        For beginners: Finds documents most similar to your question.
        For production: Optimized similarity search with Gemini embeddings.
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum similarity score (0-1, higher = more similar)
            
        Returns:
            List of similar documents with scores
        """
        if not self.vector_store:
            raise ValueError("No vector store loaded. Create or load one first.")
        
        # Perform similarity search with scores
        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=k
        )
        
        # Filter by threshold and format results
        filtered_results = []
        for doc, score in results:
            # Note: FAISS returns distance, so we convert to similarity
            similarity = 1 - (score / 2)  # Rough conversion, adjust as needed
            if similarity >= score_threshold:
                doc.metadata['similarity_score'] = similarity
                filtered_results.append(doc)
        
        logger.info(f"Found {len(filtered_results)} similar documents for query: {query[:50]}...")
        return filtered_results
    
    def _save_vector_store(self) -> None:
        """Save vector store to disk."""
        if self.vector_store:
            self.vector_store.save_local(folder_path=str(self.vector_db_path))
            logger.info(f"Vector store saved to {self.vector_db_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.
        
        Returns:
            Dictionary with vector store information
        """
        if not self.vector_store:
            return {"status": "No vector store loaded"}
        
        # Get index information
        index = self.vector_store.index
        total_vectors = index.ntotal
        
        return {
            "total_vectors": total_vectors,
            "index_type": type(index).__name__,
            "dimension": index.d,
            "vector_db_path": str(self.vector_db_path),
            "index_exists": self.index_path.exists(),
            "docs_exists": self.docs_path.exists(),
            "embedding_model": "models/embedding-001"
        }
    
    def delete_vector_store(self) -> None:
        """Delete the vector store files."""
        if self.index_path.exists():
            self.index_path.unlink()
        if self.docs_path.exists():
            self.docs_path.unlink()
        
        self.vector_store = None
        logger.info("Vector store deleted")

# Example usage
if __name__ == "__main__":
    # Test the vector store with Gemini
    print("=== Gemini Vector Store Test ===")
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY in your .env file")
        exit(1)
    
    # Create vector store service
    vector_service = VectorStoreGemini(google_api_key=api_key)
    
    # Try to load existing store
    store = vector_service.load_vector_store()
    
    if store:
        stats = vector_service.get_stats()
        print(f"Loaded vector store: {stats}")
        
        # Test search
        results = vector_service.similarity_search("test query")
        print(f"Search results: {len(results)} documents found")
    else:
        print("No existing vector store. Create one by running the full pipeline first.")
