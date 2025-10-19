"""Test configuration and utilities."""
import os
import sys
import json
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestConfig:
    """Test configuration constants."""
    
    # Test data paths
    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
    MOCK_AUTH_DIR = os.path.join(TEST_DATA_DIR, 'auth')
    
    # Mock API responses
    MOCK_SPOTIFY_RESPONSES = {
        'profile': {
            'id': 'test_user',
            'display_name': 'Test User',
            'email': 'test@example.com'
        },
        'currently_playing': {
            'is_playing': True,
            'item': {
                'name': 'Test Song',
                'artists': [{'name': 'Test Artist'}],
                'album': {'name': 'Test Album'}
            }
        }
    }
    
    MOCK_GOOGLE_RESPONSES = {
        'profile': {
            'id': 'test_google_user',
            'name': 'Test Google User',
            'email': 'test@gmail.com'
        }
    }
    
    MOCK_FACEBOOK_RESPONSES = {
        'profile': {
            'id': 'test_facebook_user',
            'name': 'Test Facebook User'
        }
    }

class MockAPIResponse:
    """Mock API response for testing."""
    
    def __init__(self, status_code: int = 200, json_data: Dict[str, Any] = None):
        self.status_code = status_code
        self._json_data = json_data or {}
    
    def json(self):
        return self._json_data
    
    @property
    def text(self):
        return json.dumps(self._json_data)

def create_mock_credentials(service: str) -> Dict[str, str]:
    """Create mock credentials for testing."""
    return {
        'client_id': f'test_{service}_client_id',
        'client_secret': f'test_{service}_client_secret',
        'redirect_uri': f'http://localhost:8081/{service}/callback',
        'access_token': f'test_{service}_access_token',
        'refresh_token': f'test_{service}_refresh_token'
    }

def mock_api_call(method: str, url: str, **kwargs) -> MockAPIResponse:
    """Mock API call for testing."""
    # Return different responses based on URL patterns
    if 'spotify' in url:
        if 'profile' in url:
            return MockAPIResponse(json_data=TestConfig.MOCK_SPOTIFY_RESPONSES['profile'])
        elif 'currently-playing' in url:
            return MockAPIResponse(json_data=TestConfig.MOCK_SPOTIFY_RESPONSES['currently_playing'])
    elif 'google' in url:
        return MockAPIResponse(json_data=TestConfig.MOCK_GOOGLE_RESPONSES['profile'])
    elif 'facebook' in url:
        return MockAPIResponse(json_data=TestConfig.MOCK_FACEBOOK_RESPONSES['profile'])
    
    return MockAPIResponse()

@pytest.fixture
def mock_requests():
    """Mock requests library for testing."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.put') as mock_put:
        
        mock_get.return_value = MockAPIResponse()
        mock_post.return_value = MockAPIResponse()
        mock_put.return_value = MockAPIResponse()
        
        yield {
            'get': mock_get,
            'post': mock_post,
            'put': mock_put
        }

@pytest.fixture
def mock_file_system():
    """Mock file system operations for testing."""
    with patch('os.path.exists') as mock_exists, \
         patch('builtins.open', create=True) as mock_open:
        
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = 'test content'
        
        yield {
            'exists': mock_exists,
            'open': mock_open
        }

@pytest.fixture
def sample_local_data():
    """Sample local data for testing."""
    return {
        'artificial-intelligence-future.txt': 'AI will revolutionize the world...',
        'blockchain-technology-impact.txt': 'Blockchain technology is transforming...',
        'climate-change-solutions.txt': 'Climate change requires immediate action...'
    }
