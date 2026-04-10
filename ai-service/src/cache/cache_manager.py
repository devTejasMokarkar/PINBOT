"""
Cache Manager

Handles caching of query results and embeddings using Redis.
"""

import json
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import timedelta
import redis
from redis.asyncio import Redis as AsyncRedis

from src.config import Config
from src.exceptions import AIServiceException

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based cache manager for AI service"""
    
    def __init__(self, config: Config):
        """Initialize cache manager with configuration"""
        self.config = config
        self.redis_client = None
        self.async_redis_client = None
        self.ttl_queries = 3600  # 1 hour for query results
        self.ttl_embeddings = 86400  # 24 hours for embeddings
        self.ttl_documents = 7200  # 2 hours for document chunks
        
        try:
            self._initialize_redis()
        except Exception as e:
            logger.warning(f"Redis not available, caching disabled: {e}")
            self.redis_client = None
            self.async_redis_client = None
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            # Redis configuration (can be extended from config)
            redis_host = "localhost"
            redis_port = 6379
            redis_db = 0
            
            # Sync Redis client
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Async Redis client
            self.async_redis_client = AsyncRedis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise AIServiceException(f"Redis connection failed: {e}")
    
    def _generate_query_key(self, question: str, k: int, model: str) -> str:
        """Generate cache key for query"""
        content = f"{question}_{k}_{model}"
        return f"query:{hashlib.md5(content.encode()).hexdigest()}"
    
    def _generate_embedding_key(self, text: str, model: str) -> str:
        """Generate cache key for embedding"""
        content = f"{text}_{model}"
        return f"embedding:{hashlib.md5(content.encode()).hexdigest()}"
    
    def _generate_document_key(self, doc_id: str) -> str:
        """Generate cache key for document"""
        return f"document:{doc_id}"
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis_client is not None
    
    async def get_query_result(self, question: str, k: int, model: str) -> Optional[Dict[str, Any]]:
        """Get cached query result"""
        if not self.is_available():
            return None
        
        try:
            key = self._generate_query_key(question, k, model)
            cached_data = await self.async_redis_client.get(key)
            
            if cached_data:
                logger.info(f"Cache hit for query: {question[:50]}...")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get query from cache: {e}")
            return None
    
    async def cache_query_result(self, question: str, k: int, model: str, result: Dict[str, Any]):
        """Cache query result"""
        if not self.is_available():
            return
        
        try:
            key = self._generate_query_key(question, k, model)
            await self.async_redis_client.setex(
                key, 
                self.ttl_queries, 
                json.dumps(result, default=str)
            )
            logger.info(f"Cached query result: {question[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to cache query result: {e}")
    
    async def get_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding"""
        if not self.is_available():
            return None
        
        try:
            key = self._generate_embedding_key(text, model)
            cached_data = await self.async_redis_client.get(key)
            
            if cached_data:
                logger.info(f"Cache hit for embedding: {text[:30]}...")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get embedding from cache: {e}")
            return None
    
    async def cache_embedding(self, text: str, model: str, embedding: List[float]):
        """Cache embedding"""
        if not self.is_available():
            return
        
        try:
            key = self._generate_embedding_key(text, model)
            await self.async_redis_client.setex(
                key,
                self.ttl_embeddings,
                json.dumps(embedding)
            )
            logger.info(f"Cached embedding: {text[:30]}...")
            
        except Exception as e:
            logger.error(f"Failed to cache embedding: {e}")
    
    async def get_document_chunk(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get cached document chunk"""
        if not self.is_available():
            return None
        
        try:
            key = self._generate_document_key(doc_id)
            cached_data = await self.async_redis_client.get(key)
            
            if cached_data:
                logger.info(f"Cache hit for document: {doc_id}")
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document from cache: {e}")
            return None
    
    async def cache_document_chunk(self, doc_id: str, chunk_data: Dict[str, Any]):
        """Cache document chunk"""
        if not self.is_available():
            return
        
        try:
            key = self._generate_document_key(doc_id)
            await self.async_redis_client.setex(
                key,
                self.ttl_documents,
                json.dumps(chunk_data, default=str)
            )
            logger.info(f"Cached document chunk: {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to cache document chunk: {e}")
    
    async def invalidate_query_cache(self, pattern: str = "*"):
        """Invalidate query cache by pattern"""
        if not self.is_available():
            return
        
        try:
            keys = await self.async_redis_client.keys(f"query:{pattern}")
            if keys:
                await self.async_redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} query cache entries")
            
        except Exception as e:
            logger.error(f"Failed to invalidate query cache: {e}")
    
    async def invalidate_document_cache(self):
        """Invalidate all document cache"""
        if not self.is_available():
            return
        
        try:
            keys = await self.async_redis_client.keys("document:*")
            if keys:
                await self.async_redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} document cache entries")
            
        except Exception as e:
            logger.error(f"Failed to invalidate document cache: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_available():
            return {"error": "Cache not available"}
        
        try:
            info = await self.async_redis_client.info()
            
            # Get key counts by type
            query_keys = len(await self.async_redis_client.keys("query:*"))
            embedding_keys = len(await self.async_redis_client.keys("embedding:*"))
            document_keys = len(await self.async_redis_client.keys("document:*"))
            
            return {
                "redis_connected": True,
                "memory_used": info.get("used_memory_human", "N/A"),
                "total_keys": info.get("db0", {}).get("keys", 0),
                "query_cache_size": query_keys,
                "embedding_cache_size": embedding_keys,
                "document_cache_size": document_keys,
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_misses", 1), 1)
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired(self):
        """Clean up expired cache entries"""
        if not self.is_available():
            return
        
        try:
            # Redis automatically handles TTL, but we can log stats
            stats = await self.get_cache_stats()
            logger.info(f"Cache cleanup completed. Stats: {stats}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup cache: {e}")
    
    async def close(self):
        """Close Redis connections"""
        try:
            if self.async_redis_client:
                await self.async_redis_client.close()
            if self.redis_client:
                self.redis_client.close()
            logger.info("Redis connections closed")
            
        except Exception as e:
            logger.error(f"Failed to close Redis connections: {e}")
