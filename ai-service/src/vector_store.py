"""
Vector Store Service using FAISS

This module handles storing and retrieving document embeddings.
For beginners: Think of this as a smart library that remembers where every piece of information is located.
For production: High-performance vector similarity search with persistence and indexing.
"""

import os
import pickle
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import numpy as np
import faiss
from langchain.schema import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.vectorstores.base import VectorStore

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Manages FAISS vector store for document embeddings.
    
    For beginners: Stores document "fingerprints" for fast similarity search.
    For production: Handles persistence, indexing, and efficient retrieval at scale.
    """
    
    def __init__(self, 
                 vector_db_path: str = "./vector_db",
                 openai_api_key: str = None):
        """
        Initialize the vector store service.
        
        Args:
            vector_db_path: Path to store FAISS index
            openai_api_key: OpenAI API key for embeddings
        """
        self.vector_db_path = Path(vector_db_path)
        self.vector_db_path.mkdir(exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key,
            model="text-embedding-ada-002"  # Most cost-effective for production
        )
        
        self.vector_store = None
        self.index_path = self.vector_db_path / "index.faiss"
        self.docs_path = self.vector_db_path / "documents.pkl"
        
    def create_vector_store(self, documents: List[Document]) -> FAISS:
        """
        Create a new vector store from documents.
        
        For beginners: Creates a searchable index from your documents.
        For production: Optimizes index creation for performance and memory usage.
        
        Args:
            documents: List of chunked documents
            
        Returns:
            FAISS vector store
        """
        if not documents:
            raise ValueError("No documents provided for vector store creation")
        
        logger.info(f"Creating vector store from {len(documents)} documents")
        
        # Create FAISS index
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
                         score_threshold: float = 0.5) -> List[Document]:
        """
        Search for similar documents.
        
        For beginners: Finds documents most similar to your question.
        For production: Optimized similarity search with scoring and filtering.
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum similarity score
            
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
            if score <= score_threshold:  # Lower score = more similar in FAISS
                doc.metadata['similarity_score'] = score
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
            "docs_exists": self.docs_path.exists()
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
    # Test the vector store
    print("=== Vector Store Test ===")
    
    # You'll need to set your OpenAI API key
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY in your .env file")
        exit(1)
    
    # Create vector store service
    vector_service = VectorStoreService(openai_api_key=api_key)
    
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
