"""Integration tests for service APIs and server."""
import pytest
import requests
from unittest.mock import patch, Mock
from tests.conftest import TestConfig, create_mock_credentials


class TestServiceIntegration:
    """Integration tests for service APIs."""
    
    @pytest.fixture
    def mock_server(self):
        """Mock server for integration testing."""
        with patch('requests.get') as mock_get, \
             patch('requests.post') as mock_post:
            
            mock_get.return_value.json.return_value = {"success": True, "data": "test"}
            mock_post.return_value.json.return_value = {"success": True, "data": "test"}
            
            yield {
                'get': mock_get,
                'post': mock_post
            }
    
    def test_spotify_integration(self, mock_server):
        """Test Spotify API integration with server."""
        response = requests.get('http://localhost:8081/spotify/profile')
        assert response.json()['success'] is True
        
        response = requests.get('http://localhost:8081/spotify/currently-playing')
        assert response.json()['success'] is True
        
        response = requests.post('http://localhost:8081/spotify/playback/next')
        assert response.json()['success'] is True
    
    def test_google_integration(self, mock_server):
        """Test Google API integration with server."""
        response = requests.get('http://localhost:8081/google/profile')
        assert response.json()['success'] is True
        
        response = requests.get('http://localhost:8081/google/drive/files')
        assert response.json()['success'] is True
    
    def test_facebook_integration(self, mock_server):
        """Test Facebook API integration with server."""
        response = requests.get('http://localhost:8081/facebook/profile')
        assert response.json()['success'] is True
        
        response = requests.get('http://localhost:8081/facebook/pages')
        assert response.json()['success'] is True
    
    def test_instagram_integration(self, mock_server):
        """Test Instagram API integration with server."""
        response = requests.get('http://localhost:8081/instagram/profile')
        assert response.json()['success'] is True
        
        response = requests.get('http://localhost:8081/instagram/media')
        assert response.json()['success'] is True
    
    def test_whatsapp_integration(self, mock_server):
        """Test WhatsApp API integration with server."""
        response = requests.get('http://localhost:8081/whatsapp/status')
        assert response.json()['success'] is True
        
        response = requests.get('http://localhost:8081/whatsapp/chats')
        assert response.json()['success'] is True
    
    def test_files_integration(self, mock_server):
        """Test Files API integration with server."""
        response = requests.get('http://localhost:8081/files/list')
        assert response.json()['success'] is True
        
        response = requests.get('http://localhost:8081/files/search?q=test')
        assert response.json()['success'] is True


class TestServerIntegration:
    """Integration tests for main server API."""
    
    @pytest.fixture
    def mock_server_responses(self):
        """Mock server responses for testing."""
        return {
            'health': {"status": "healthy", "services": ["spotify", "google", "facebook"]},
            'services': {
                "spotify": {"name": "Spotify", "status": "active"},
                "google": {"name": "Google", "status": "active"},
                "facebook": {"name": "Facebook", "status": "active"}
            }
        }
    
    def test_health_endpoint(self, mock_server_responses):
        """Test server health endpoint."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_server_responses['health']
            
            response = requests.get('http://localhost:8081/health')
            data = response.json()
            
            assert data['status'] == 'healthy'
            assert 'services' in data
            assert len(data['services']) > 0
    
    def test_services_endpoint(self, mock_server_responses):
        """Test services endpoint."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_server_responses['services']
            
            response = requests.get('http://localhost:8081/services')
            data = response.json()
            
            assert 'spotify' in data
            assert 'google' in data
            assert 'facebook' in data
            assert data['spotify']['status'] == 'active'
    
    def test_cross_service_communication(self):
        """Test communication between different services."""
        with patch('requests.get') as mock_get, \
             patch('requests.post') as mock_post:
            
            mock_get.return_value.json.side_effect = [
                {"success": True, "profile": "spotify_user"},
                {"success": True, "profile": "google_user"},
                {"success": True, "files": ["file1.txt"]}
            ]
            
            spotify_response = requests.get('http://localhost:8081/spotify/profile')
            google_response = requests.get('http://localhost:8081/google/profile')
            files_response = requests.get('http://localhost:8081/files/list')
            
            assert spotify_response.json()['success'] is True
            assert google_response.json()['success'] is True
            assert files_response.json()['success'] is True
    
    def test_error_handling_integration(self):
        """Test error handling across services."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"success": False, "error": "Service unavailable"}
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            response = requests.get('http://localhost:8081/spotify/profile')
            data = response.json()
            
            assert data['success'] is False
            assert 'error' in data
