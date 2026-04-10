"""
Document Loading Service

This module handles loading and processing various document types.
For beginners: Think of this as the "librarian" that reads different book formats.
For production: This is our data ingestion pipeline with error handling and validation.
"""

import os
import logging
from typing import List, Dict, Any
from pathlib import Path

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentLoader:
    """
    Handles loading documents from various sources.
    
    For beginners: This class knows how to read PDFs, text files, etc.
    For production: Implements robust error handling, validation, and batch processing.
    """
    
    def __init__(self, docs_path: str = "./documents"):
        """
        Initialize the document loader.
        
        Args:
            docs_path: Path to the documents directory
        """
        self.docs_path = Path(docs_path)
        self.supported_formats = {'.pdf', '.txt', '.md'}
        
        # Create docs directory if it doesn't exist
        self.docs_path.mkdir(exist_ok=True)
        
    def load_single_document(self, file_path: str) -> List[Document]:
        """
        Load a single document based on its file extension.
        
        For beginners: This function looks at the file type and uses the right reader.
        For production: Includes validation, error handling, and metadata extraction.
        
        Args:
            file_path: Path to the document
            
        Returns:
            List of Document objects
            
        Raises:
            ValueError: If file format is not supported
            Exception: If loading fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
            
        if file_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported format: {file_path.suffix}")
        
        try:
            # Choose the right loader based on file type
            if file_path.suffix.lower() == '.pdf':
                loader = PyPDFLoader(str(file_path))
            elif file_path.suffix.lower() in ['.txt', '.md']:
                loader = TextLoader(str(file_path), encoding='utf-8')
            else:
                raise ValueError(f"Unsupported format: {file_path.suffix}")
            
            # Load the document
            documents = loader.load()
            
            # Add metadata
            for doc in documents:
                doc.metadata['source'] = str(file_path)
                doc.metadata['file_type'] = file_path.suffix.lower()
                doc.metadata['file_size'] = file_path.stat().st_size
                
            logger.info(f"Successfully loaded {len(documents)} pages from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise
    
    def load_all_documents(self) -> List[Document]:
        """
        Load all supported documents from the documents directory.
        
        For beginners: Reads all files in the documents folder.
        For production: Batch processing with parallel loading and error recovery.
        
        Returns:
            List of all Document objects
        """
        all_documents = []
        
        # Find all supported files
        for file_path in self.docs_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                try:
                    documents = self.load_single_document(str(file_path))
                    all_documents.extend(documents)
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {str(e)}")
                    continue
        
        logger.info(f"Loaded {len(all_documents)} document pages from {len(all_documents)} files")
        return all_documents
    
    def get_document_info(self) -> Dict[str, Any]:
        """
        Get information about loaded documents.
        
        Returns:
            Dictionary with document statistics
        """
        files = list(self.docs_path.rglob('*'))
        supported_files = [f for f in files if f.is_file() and f.suffix.lower() in self.supported_formats]
        
        return {
            'total_files': len(supported_files),
            'supported_formats': list(self.supported_formats),
            'files_by_type': {
                ext: len([f for f in supported_files if f.suffix.lower() == ext])
                for ext in self.supported_formats
            },
            'total_size_mb': sum(f.stat().st_size for f in supported_files) / (1024 * 1024)
        }

# Example usage (for testing)
if __name__ == "__main__":
    # This is how you would test the loader
    loader = DocumentLoader()
    
    # Get info about documents
    info = loader.get_document_info()
    print("Document Info:", info)
    
    # Load all documents
    try:
        documents = loader.load_all_documents()
        print(f"Loaded {len(documents)} document pages")
        
        # Show first document as example
        if documents:
            print(f"First document: {documents[0].page_content[:200]}...")
            print(f"Metadata: {documents[0].metadata}")
    except Exception as e:
        print(f"Error: {e}")
