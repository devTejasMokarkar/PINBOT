"""
Async Document Processor

Handles asynchronous document processing with batch operations and progress tracking.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

from langchain_core.documents import Document

from src.document_loader import DocumentLoader
from src.text_chunker import TextChunker
from src.vector_store_optimized import OptimizedVectorStoreGemini
from src.cache.cache_manager import CacheManager
from src.exceptions import DocumentProcessingException

logger = logging.getLogger(__name__)

@dataclass
class ProcessingProgress:
    """Progress tracking for document processing"""
    total_files: int
    processed_files: int
    total_chunks: int
    processed_chunks: int
    current_file: str
    start_time: datetime
    errors: List[str]
    
    @property
    def progress_percentage(self) -> float:
        return (self.processed_files / max(self.total_files, 1)) * 100
    
    @property
    def elapsed_time(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()

class AsyncDocumentProcessor:
    """
    Asynchronous document processor with batch operations and progress tracking.
    
    Features:
    - Parallel document loading
    - Batch chunking
    - Progress tracking
    - Error handling and recovery
    - Memory optimization
    """
    
    def __init__(self, 
                 document_loader: DocumentLoader,
                 text_chunker: TextChunker,
                 vector_store: OptimizedVectorStoreGemini,
                 cache_manager: Optional[CacheManager] = None,
                 max_workers: int = 4):
        """
        Initialize async document processor.
        
        Args:
            document_loader: Document loading service
            text_chunker: Text chunking service
            vector_store: Vector store service
            cache_manager: Cache manager
            max_workers: Maximum number of worker threads
        """
        self.document_loader = document_loader
        self.text_chunker = text_chunker
        self.vector_store = vector_store
        self.cache_manager = cache_manager
        self.max_workers = max_workers
        
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.progress: Optional[ProcessingProgress] = None
        self.progress_callbacks: List[Callable] = []
    
    def add_progress_callback(self, callback: Callable[[ProcessingProgress], None]):
        """Add callback for progress updates."""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self):
        """Notify all progress callbacks."""
        if self.progress:
            for callback in self.progress_callbacks:
                try:
                    callback(self.progress)
                except Exception as e:
                    logger.error(f"Progress callback failed: {e}")
    
    async def process_documents_async(self, 
                                    documents_path: str,
                                    batch_size: int = 50,
                                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process documents asynchronously with batch operations.
        
        Args:
            documents_path: Path to documents directory
            batch_size: Number of documents to process in each batch
            progress_callback: Optional progress callback function
            
        Returns:
            Processing results with statistics
        """
        try:
            # Initialize progress tracking
            documents_path = Path(documents_path)
            all_files = self._get_supported_files(documents_path)
            
            if not all_files:
                raise DocumentProcessingException("No supported documents found")
            
            self.progress = ProcessingProgress(
                total_files=len(all_files),
                processed_files=0,
                total_chunks=0,
                processed_chunks=0,
                current_file="",
                start_time=datetime.now(),
                errors=[]
            )
            
            if progress_callback:
                self.add_progress_callback(progress_callback)
            
            logger.info(f"Starting async processing of {len(all_files)} documents")
            
            # Process files in batches
            all_documents = []
            total_chunks = 0
            
            for i in range(0, len(all_files), batch_size):
                batch_files = all_files[i:i + batch_size]
                
                # Load batch asynchronously
                batch_documents = await self._load_document_batch(batch_files)
                all_documents.extend(batch_documents)
                
                # Update progress
                self.progress.processed_files = len(batch_files) + i
                self.progress.current_file = f"Batch {i//batch_size + 1}"
                self._notify_progress()
                
                logger.info(f"Loaded batch {i//batch_size + 1}: {len(batch_documents)} pages")
            
            # Chunk all documents
            logger.info("Starting document chunking...")
            chunked_documents = await self._chunk_documents_async(all_documents)
            total_chunks = len(chunked_documents)
            
            self.progress.total_chunks = total_chunks
            self.progress.processed_chunks = total_chunks
            self._notify_progress()
            
            # Create vector store
            logger.info("Creating vector store...")
            await self.vector_store.create_vector_store(chunked_documents)
            
            # Cache processing results
            if self.cache_manager:
                await self._cache_processing_results(len(all_files), total_chunks)
            
            # Generate final report
            processing_time = self.progress.elapsed_time
            
            result = {
                "status": "success",
                "files_processed": len(all_files),
                "pages_loaded": len(all_documents),
                "chunks_created": total_chunks,
                "processing_time": processing_time,
                "files_per_second": len(all_files) / max(processing_time, 1),
                "errors": self.progress.errors,
                "performance_metrics": self.vector_store.get_performance_metrics()
            }
            
            logger.info(f"Async processing completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Async document processing failed: {e}")
            raise DocumentProcessingException(f"Processing failed: {e}")
        
        finally:
            self.progress = None
    
    def _get_supported_files(self, documents_path: Path) -> List[Path]:
        """Get list of supported document files."""
        supported_extensions = {'.pdf', '.txt', '.md'}
        files = []
        
        for ext in supported_extensions:
            files.extend(documents_path.glob(f"*{ext}"))
        
        return sorted(files)
    
    async def _load_document_batch(self, file_paths: List[Path]) -> List[Document]:
        """Load a batch of documents asynchronously."""
        tasks = []
        
        for file_path in file_paths:
            task = asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._load_single_document,
                file_path
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        documents = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"Failed to load {file_paths[i]}: {result}"
                logger.error(error_msg)
                if self.progress:
                    self.progress.errors.append(error_msg)
            else:
                documents.extend(result)
        
        return documents
    
    def _load_single_document(self, file_path: Path) -> List[Document]:
        """Load a single document."""
        try:
            return self.document_loader.load_single_document(str(file_path))
        except Exception as e:
            raise DocumentProcessingException(f"Failed to load {file_path}: {e}")
    
    async def _chunk_documents_async(self, documents: List[Document]) -> List[Document]:
        """Chunk documents asynchronously."""
        # Process in batches to manage memory
        batch_size = 100
        all_chunks = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Process batch asynchronously
            batch_chunks = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.text_chunker.chunk_documents,
                batch
            )
            
            all_chunks.extend(batch_chunks)
            
            # Update progress
            if self.progress:
                self.progress.processed_chunks = len(all_chunks)
                self.progress.current_file = f"Chunking batch {i//batch_size + 1}"
                self._notify_progress()
        
        return all_chunks
    
    async def _cache_processing_results(self, files_processed: int, chunks_created: int):
        """Cache processing results for future reference."""
        try:
            cache_data = {
                "files_processed": files_processed,
                "chunks_created": chunks_created,
                "timestamp": datetime.now().isoformat(),
                "processing_stats": self.vector_store.get_performance_metrics()
            }
            
            await self.cache_manager.cache_document_chunk(
                "last_processing_result",
                cache_data
            )
            
        except Exception as e:
            logger.error(f"Failed to cache processing results: {e}")
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        stats = {
            "current_progress": None,
            "vector_store_metrics": self.vector_store.get_performance_metrics(),
            "cache_stats": None
        }
        
        if self.progress:
            stats["current_progress"] = {
                "files_processed": self.progress.processed_files,
                "total_files": self.progress.total_files,
                "progress_percentage": self.progress.progress_percentage,
                "elapsed_time": self.progress.elapsed_time,
                "current_file": self.progress.current_file,
                "errors_count": len(self.progress.errors)
            }
        
        if self.cache_manager:
            stats["cache_stats"] = await self.cache_manager.get_cache_stats()
        
        return stats
    
    async def cancel_processing(self):
        """Cancel current processing operation."""
        if self.progress:
            self.progress.errors.append("Processing cancelled by user")
            logger.info("Document processing cancelled")
    
    async def close(self):
        """Clean up resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Async document processor closed")
