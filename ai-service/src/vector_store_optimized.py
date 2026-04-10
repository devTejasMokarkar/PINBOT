"""
Optimized Vector Store Service with Caching

Enhanced vector store with caching, batch processing, and performance optimizations.
"""

import os
import pickle
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import faiss
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS

from src.cache.cache_manager import CacheManager
from src.exceptions import VectorStoreException

logger = logging.getLogger(__name__)

class OptimizedVectorStoreGemini:
    """
    Optimized vector store with caching and performance improvements.
    
    Features:
    - Redis caching for embeddings and search results
    - Batch processing for embeddings
    - Async operations
    - Connection pooling
    - Performance monitoring
    """
    
    def __init__(self, 
                 vector_db_path: str = "./vector_db",
                 google_api_key: str = None,
                 cache_manager: Optional[CacheManager] = None):
        """
        Initialize the optimized vector store.
        
        Args:
            vector_db_path: Path to store FAISS index
            google_api_key: Google Gemini API key
            cache_manager: Redis cache manager instance
        """
        self.vector_db_path = Path(vector_db_path)
        self.vector_db_path.mkdir(exist_ok=True)
        
        # Cache manager
        self.cache_manager = cache_manager
        
        # Thread pool for batch operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize Gemini embeddings with optimizations
        self.embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=google_api_key,
            model="models/gemini-embedding-001",
            batch_size=10  # Process embeddings in batches
        )
        
        # Initialize chat model
        self.chat_model = ChatGoogleGenerativeAI(
            google_api_key=google_api_key,
            model="gemini-2.5-flash",
            temperature=0.1,
            max_retries=0
        )
        
        self.vector_store = None
        self.index_path = self.vector_db_path / "index.faiss"
        self.docs_path = self.vector_db_path / "documents.pkl"
        
        # Performance metrics
        self.metrics = {
            "searches_performed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "embeddings_generated": 0,
            "avg_search_time": 0.0
        }
        
        logger.info("Optimized vector store initialized")
    
    async def create_vector_store(self, documents: List[Document]) -> FAISS:
        """
        Create vector store with batch processing and caching.
        
        Args:
            documents: List of documents to embed
            
        Returns:
            FAISS vector store
        """
        if not documents:
            raise VectorStoreException("No documents provided for vector store creation")
        
        try:
            logger.info(f"Creating optimized vector store from {len(documents)} documents")
            
            # Process documents in batches
            batch_size = 50
            all_embeddings = []
            processed_docs = []
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_embeddings = await self._process_document_batch(batch)
                all_embeddings.extend(batch_embeddings)
                processed_docs.extend(batch)
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            # Create FAISS index with all embeddings
            embeddings_array = np.array(all_embeddings).astype('float32')
            
            # Create optimized FAISS index
            dimension = embeddings_array.shape[1]
            index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings_array)
            index.add(embeddings_array)
            
            # Create vector store
            self.vector_store = FAISS(
                embedding_function=self.embeddings,
                index=index,
                docstore=FAISS.InMemoryDocstore(),
                index_to_docstore_id={}
            )
            
            # Add documents to store
            self.vector_store.add_documents(processed_docs)
            
            # Save to disk
            await self._save_vector_store()
            
            # Cache document chunks
            if self.cache_manager:
                await self._cache_documents(processed_docs)
            
            logger.info(f"Optimized vector store created with {len(processed_docs)} documents")
            return self.vector_store
            
        except Exception as e:
            logger.error(f"Failed to create optimized vector store: {e}")
            raise VectorStoreException(f"Vector store creation failed: {e}")
    
    async def _process_document_batch(self, documents: List[Document]) -> List[List[float]]:
        """
        Process a batch of documents to generate embeddings.
        
        Args:
            documents: Batch of documents
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for doc in documents:
            # Check cache first
            if self.cache_manager:
                cached_embedding = await self.cache_manager.get_embedding(
                    doc.page_content, 
                    "models/gemini-embedding-001"
                )
                if cached_embedding:
                    embeddings.append(cached_embedding)
                    continue
            
            # Generate embedding if not cached
            try:
                embedding = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.embeddings.embed_query,
                    doc.page_content
                )
                embeddings.append(embedding)
                
                # Cache the embedding
                if self.cache_manager:
                    await self.cache_manager.cache_embedding(
                        doc.page_content,
                        "models/gemini-embedding-001",
                        embedding
                    )
                
                self.metrics["embeddings_generated"] += 1
                
            except Exception as e:
                logger.error(f"Failed to generate embedding for document: {e}")
                # Use zero embedding as fallback
                embeddings.append([0.0] * 768)  # Gemini embedding dimension
        
        return embeddings
    
    async def similarity_search(self, 
                              query: str, 
                              k: int = 4, 
                              score_threshold: float = 0.6) -> List[Document]:
        """
        Optimized similarity search with caching.
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar documents with scores
        """
        import time
        start_time = time.time()
        
        try:
            # Check cache for search results
            if self.cache_manager:
                cache_key = f"search_{hashlib.md5(f'{query}_{k}_{score_threshold}'.encode()).hexdigest()}"
                cached_result = await self.cache_manager.get_document_chunk(cache_key)
                if cached_result:
                    self.metrics["cache_hits"] += 1
                    logger.info(f"Cache hit for search: {query[:50]}...")
                    return [Document(**doc) for doc in cached_result["documents"]]
            
            self.metrics["cache_misses"] += 1
            
            # Load vector store if not loaded
            if not self.vector_store:
                await self.load_vector_store()
            
            if not self.vector_store:
                raise VectorStoreException("Vector store not available")
            
            # Generate query embedding
            query_embedding = await self._get_query_embedding(query)
            
            # Perform search
            results = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.vector_store.similarity_search_with_score,
                query,
                k
            )
            
            # Filter by score threshold and format results
            filtered_results = []
            for doc, score in results:
                if score >= score_threshold:
                    doc.metadata['similarity_score'] = float(score)
                    filtered_results.append(doc)
            
            # Cache the results
            if self.cache_manager and filtered_results:
                cache_data = {
                    "documents": [doc.dict() for doc in filtered_results],
                    "query": query,
                    "k": k,
                    "score_threshold": score_threshold
                }
                await self.cache_manager.cache_document_chunk(cache_key, cache_data)
            
            # Update metrics
            search_time = time.time() - start_time
            self.metrics["searches_performed"] += 1
            self.metrics["avg_search_time"] = (
                (self.metrics["avg_search_time"] * (self.metrics["searches_performed"] - 1) + search_time) /
                self.metrics["searches_performed"]
            )
            
            logger.info(f"Search completed in {search_time:.3f}s, found {len(filtered_results)} results")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise VectorStoreException(f"Search failed: {e}")
    
    async def _get_query_embedding(self, query: str) -> List[float]:
        """Get query embedding with caching."""
        # Check cache first
        if self.cache_manager:
            cached_embedding = await self.cache_manager.get_embedding(
                query, 
                "models/gemini-embedding-001"
            )
            if cached_embedding:
                return cached_embedding
        
        # Generate embedding
        embedding = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.embeddings.embed_query,
            query
        )
        
        # Cache the embedding
        if self.cache_manager:
            await self.cache_manager.cache_embedding(
                query,
                "models/gemini-embedding-001",
                embedding
            )
        
        self.metrics["embeddings_generated"] += 1
        return embedding
    
    async def load_vector_store(self) -> Optional[FAISS]:
        """Load existing vector store with optimizations."""
        try:
            if not self.index_path.exists() or not self.docs_path.exists():
                logger.info("No existing vector store found")
                return None
            
            # Load in parallel
            index_future = asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._load_index
            )
            
            docs_future = asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._load_documents
            )
            
            index, docs = await asyncio.gather(index_future, docs_future)
            
            if index and docs:
                self.vector_store = FAISS(
                    embedding_function=self.embeddings,
                    index=index,
                    docstore=docs,
                    index_to_docstore_id={i: i for i in range(len(docs))}
                )
                
                logger.info(f"Loaded optimized vector store from {self.vector_db_path}")
                return self.vector_store
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return None
    
    def _load_index(self):
        """Load FAISS index."""
        return faiss.read_index(str(self.index_path))
    
    def _load_documents(self):
        """Load documents from pickle file."""
        with open(self.docs_path, 'rb') as f:
            return pickle.load(f)
    
    async def _save_vector_store(self):
        """Save vector store to disk."""
        if not self.vector_store:
            return
        
        try:
            # Save index and documents in parallel
            index_future = asyncio.get_event_loop().run_in_executor(
                self.executor,
                faiss.write_index,
                self.vector_store.index,
                str(self.index_path)
            )
            
            docs_future = asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._save_documents,
                self.vector_store.docstore
            )
            
            await asyncio.gather(index_future, docs_future)
            logger.info(f"Saved vector store to {self.vector_db_path}")
            
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
    
    def _save_documents(self, docstore):
        """Save documents to pickle file."""
        with open(self.docs_path, 'wb') as f:
            pickle.dump(docstore, f)
    
    async def _cache_documents(self, documents: List[Document]):
        """Cache document chunks for faster retrieval."""
        if not self.cache_manager:
            return
        
        try:
            for i, doc in enumerate(documents):
                doc_id = f"doc_{i}"
                await self.cache_manager.cache_document_chunk(doc_id, {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            logger.info(f"Cached {len(documents)} document chunks")
            
        except Exception as e:
            logger.error(f"Failed to cache documents: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        cache_hit_rate = 0
        if self.metrics["cache_hits"] + self.metrics["cache_misses"] > 0:
            cache_hit_rate = self.metrics["cache_hits"] / (
                self.metrics["cache_hits"] + self.metrics["cache_misses"]
            )
        
        return {
            **self.metrics,
            "cache_hit_rate": cache_hit_rate,
            "vector_store_loaded": self.vector_store is not None,
            "cache_enabled": self.cache_manager is not None
        }
    
    async def clear_cache(self):
        """Clear all cached data."""
        if self.cache_manager:
            await self.cache_manager.invalidate_document_cache()
            await self.cache_manager.invalidate_query_cache()
            logger.info("Vector store cache cleared")
    
    async def close(self):
        """Clean up resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Optimized vector store closed")
