"""
Pytest Configuration and Fixtures

Shared test configuration, fixtures, and utilities.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, Generator

# Test fixtures
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_config(temp_dir: Path) -> Dict[str, Any]:
    """Mock configuration for testing."""
    return {
        "database": {
            "vector_db_path": str(temp_dir / "vector_db"),
            "docs_path": str(temp_dir / "documents"),
            "uploads_path": str(temp_dir / "uploads")
        },
        "ai": {
            "google_api_key": "test-api-key",
            "chat_model": "gemini-2.5-flash",
            "embedding_model": "models/gemini-embedding-001",
            "temperature": 0.1,
            "max_retries": 0,
            "chunk_size": 1000,
            "chunk_overlap": 200
        },
        "api": {
            "host": "127.0.0.1",
            "port": 8000,
            "debug": True,
            "reload": False,
            "workers": 1
        },
        "quota": {
            "daily_limit": 20,
            "minute_limit": 15,
            "enable_tracking": True
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file_path": None
        }
    }

@pytest.fixture
def sample_documents() -> list:
    """Sample documents for testing."""
    return [
        {
            "content": "This is a test document about artificial intelligence and machine learning.",
            "metadata": {"source": "test1.txt", "page": 1}
        },
        {
            "content": "Python is a popular programming language for data science and AI development.",
            "metadata": {"source": "test2.txt", "page": 1}
        },
        {
            "content": "Machine learning algorithms can be classified into supervised and unsupervised learning.",
            "metadata": {"source": "test3.txt", "page": 1}
        }
    ]

@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    mock_client.keys.return_value = []
    mock_client.delete.return_value = 1
    mock_client.info.return_value = {
        "used_memory_human": "1M",
        "db0": {"keys": 100},
        "keyspace_hits": 80,
        "keyspace_misses": 20
    }
    return mock_client

@pytest.fixture
def mock_embeddings():
    """Mock Gemini embeddings for testing."""
    mock_emb = Mock()
    mock_emb.embed_query.return_value = [0.1] * 768  # 768-dimensional embedding
    mock_emb.embed_documents.return_value = [[0.1] * 768 for _ in range(3)]
    return mock_emb

@pytest.fixture
def mock_chat_model():
    """Mock Gemini chat model for testing."""
    mock_model = AsyncMock()
    mock_response = Mock()
    mock_response.content = "This is a test response from the AI model."
    mock_model.invoke.return_value = mock_response
    return mock_model

@pytest.fixture
def mock_faiss_index():
    """Mock FAISS index for testing."""
    mock_index = Mock()
    mock_index.ntotal = 100
    mock_index.d = 768
    return mock_index

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_psutil():
    """Mock psutil for performance monitoring tests."""
    mock_cpu = Mock()
    mock_cpu.percent.return_value = 45.0
    
    mock_memory = Mock()
    mock_memory.percent = 62.8
    mock_memory.used = 1024 * 1024 * 1024  # 1GB
    
    mock_disk = Mock()
    mock_disk.percent = 75.0
    
    mock_psutil = Mock()
    mock_psutil.cpu_percent.return_value = 45.0
    mock_psutil.virtual_memory.return_value = mock_memory
    mock_psutil.disk_usage.return_value = mock_disk
    
    return mock_psutil

# Test utilities
def create_test_file(temp_dir: Path, filename: str, content: str) -> Path:
    """Create a test file with given content."""
    file_path = temp_dir / filename
    file_path.write_text(content)
    return file_path

def create_test_pdf(temp_dir: Path, filename: str) -> Path:
    """Create a minimal test PDF file."""
    # For testing, we'll create a simple text file with .pdf extension
    # In real tests, you might want to use a proper PDF library
    file_path = temp_dir / filename
    file_path.write_text("%PDF-1.4\n%Test PDF content\n")
    return file_path

async def async_wait(condition_func, timeout: float = 5.0, interval: float = 0.1):
    """Wait for an async condition to be true."""
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        if condition_func():
            return True
        await asyncio.sleep(interval)
    return False

# Test markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "redis: mark test as requiring Redis"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to tests in test_unit directory
        if "test_unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to tests in test_integration directory
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker to tests in test_performance directory
        elif "test_performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
