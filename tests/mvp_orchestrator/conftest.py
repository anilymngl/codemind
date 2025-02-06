"""Common test fixtures and configurations for CodeMind tests"""

import pytest
import logging
import asyncio
from typing import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime

# Configure logging for tests
@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for all tests"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )

# Async test utilities
@pytest.fixture
async def event_loop():
    """Create an event loop for each test case"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_sleep():
    """Mock asyncio.sleep for faster tests"""
    original_sleep = asyncio.sleep
    sleep_times = []
    
    async def mock_sleep_fn(delay: float):
        sleep_times.append(delay)
        await original_sleep(0)  # Use minimal delay in tests
        
    asyncio.sleep = mock_sleep_fn
    yield sleep_times
    asyncio.sleep = original_sleep

# Mock API responses
@dataclass
class MockResponse:
    """Mock API response for testing"""
    status: int
    content: str
    headers: dict = None
    
    def json(self):
        """Return response content as JSON"""
        import json
        return json.loads(self.content)

@pytest.fixture
def mock_success_response():
    """Create a successful mock response"""
    return MockResponse(
        status=200,
        content='{"status": "success"}',
        headers={'content-type': 'application/json'}
    )

@pytest.fixture
def mock_error_response():
    """Create an error mock response"""
    return MockResponse(
        status=429,  # Rate limit error
        content='{"error": "rate_limit_exceeded"}',
        headers={'retry-after': '30'}
    )

# Test data utilities
@dataclass
class TestContext:
    """Context object for sharing data between tests"""
    start_time: datetime = None
    data: dict = None
    
    def __post_init__(self):
        self.start_time = datetime.now()
        self.data = {}

@pytest.fixture
def test_context():
    """Create a test context for sharing data"""
    return TestContext()

# Cleanup utilities
@pytest.fixture(autouse=True)
async def cleanup():
    """Clean up after each test"""
    yield
    # Add any necessary cleanup code here
    await asyncio.sleep(0)  # Allow any pending tasks to complete 