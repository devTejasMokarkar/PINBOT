"""
Text Chunking Service

This module breaks documents into optimal-sized chunks for retrieval.
For beginners: Think of this as splitting a long book into readable paragraphs.
For production: Implements adaptive chunking strategies based on content type.
"""

import logging
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter

logger = logging.getLogger(__name__)

class TextChunker:
    """
    Handles text chunking for optimal RAG performance.
    
    For beginners: Splits long documents into smaller, manageable pieces.
    For production: Implements multiple chunking strategies with metadata preservation.
    """
    
    def __init__(self):
        """
        Initialize chunkers for different use cases.
        """
        # For general text - balanced approach
        self.general_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # Small chunks for small collections
            chunk_overlap=50,  # Maintain context
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # For code/structured content
        self.code_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=30,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Token-based splitter (for production when using token limits)
        self.token_splitter = TokenTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            model_name="gpt-3.5-turbo"
        )
    
    def chunk_documents(self, 
                       documents: List[Document], 
                       strategy: str = "general") -> List[Document]:
        """
        Chunk documents using the specified strategy.
        
        Args:
            documents: List of documents to chunk
            strategy: Chunking strategy ("general", "code", "token")
            
        Returns:
            List of chunked documents
        """
        if not documents:
            return []
        
        # Choose splitter based on strategy
        splitter = self._get_splitter(strategy)
        
        # Add file type detection for adaptive chunking
        chunked_docs = []
        for doc in documents:
            # Detect content type
            content_type = self._detect_content_type(doc)
            
            # Use appropriate splitter
            if content_type == "code":
                chunks = self.code_splitter.split_documents([doc])
            else:
                chunks = splitter.split_documents([doc])
            
            # Add chunk metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    'chunk_id': f"{doc.metadata.get('source', 'unknown')}_chunk_{i}",
                    'chunk_index': i,
                    'chunk_strategy': strategy,
                    'content_type': content_type,
                    'parent_doc': doc.metadata.get('source', 'unknown')
                })
            
            chunked_docs.extend(chunks)
        
        logger.info(f"Chunked {len(documents)} documents into {len(chunked_docs)} chunks")
        return chunked_docs
    
    def _get_splitter(self, strategy: str):
        """Get the appropriate splitter for the strategy."""
        splitters = {
            "general": self.general_splitter,
            "code": self.code_splitter,
            "token": self.token_splitter
        }
        return splitters.get(strategy, self.general_splitter)
    
    def _detect_content_type(self, doc: Document) -> str:
        """
        Detect the type of content for adaptive chunking.
        
        For beginners: Different content needs different chunking.
        For production: Improves retrieval accuracy by using optimal chunking per content type.
        """
        content = doc.page_content.lower()
        file_type = doc.metadata.get('file_type', '')
        
        # Code detection
        code_indicators = ['def ', 'function ', 'class ', 'import ', 'var ', 'const ', 'let ']
        if any(indicator in content for indicator in code_indicators):
            return "code"
        
        # Structured data detection
        if file_type in ['.json', '.xml', '.csv']:
            return "structured"
        
        # Default to general text
        return "general"
    
    def get_chunking_stats(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Get statistics about chunking results.
        
        Returns:
            Dictionary with chunking statistics
        """
        if not documents:
            return {}
        
        chunk_lengths = [len(doc.page_content) for doc in documents]
        
        return {
            'total_chunks': len(documents),
            'avg_chunk_length': sum(chunk_lengths) / len(chunk_lengths),
            'min_chunk_length': min(chunk_lengths),
            'max_chunk_length': max(chunk_lengths),
            'content_types': list(set(doc.metadata.get('content_type', 'general') for doc in documents)),
            'strategies_used': list(set(doc.metadata.get('chunk_strategy', 'general') for doc in documents))
        }

# Example usage
if __name__ == "__main__":
    # Test the chunker
    from document_loader import DocumentLoader
    
    print("=== Text Chunker Test ===")
    
    # Load documents
    loader = DocumentLoader()
    docs = loader.load_all_documents()
    
    if docs:
        # Initialize chunker
        chunker = TextChunker()
        
        # Chunk documents
        chunked_docs = chunker.chunk_documents(docs, strategy="general")
        
        # Show stats
        stats = chunker.get_chunking_stats(chunked_docs)
        print(f"Chunking stats: {stats}")
        
        # Show example chunk
        if chunked_docs:
            print(f"\nExample chunk:")
            print(f"Content: {chunked_docs[0].page_content[:200]}...")
            print(f"Metadata: {chunked_docs[0].metadata}")
    else:
        print("No documents to test")
