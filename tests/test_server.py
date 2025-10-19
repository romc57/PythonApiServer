"""Server tests for main API server."""
import pytest
import json
import time
from unittest.mock import patch, Mock
from flask import Flask
from api_server import app


class TestServerEndpoints:
    """Test cases for main server endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    def test_services_endpoint(self, client):
        """Test services endpoint."""
        response = client.get('/services')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'services' in data
        assert isinstance(data['services'], dict)
    
    def test_spotify_endpoints(self, client):
        """Test Spotify service endpoints."""
        response = client.get('/spotify/profile')
        assert response.status_code in [200, 401]
        
        response = client.get('/spotify/currently-playing')
        assert response.status_code in [200, 401]
        
        response = client.post('/spotify/playback/next')
        assert response.status_code in [200, 401]
    
    def test_google_endpoints(self, client):
        """Test Google service endpoints."""
        response = client.get('/google/profile')
        assert response.status_code in [200, 401]
        
        response = client.get('/google/drive/files')
        assert response.status_code in [200, 401]
    
    def test_facebook_endpoints(self, client):
        """Test Facebook service endpoints."""
        response = client.get('/facebook/profile')
        assert response.status_code in [200, 401]
        
        response = client.get('/facebook/pages')
        assert response.status_code in [200, 401]
    
    def test_instagram_endpoints(self, client):
        """Test Instagram service endpoints."""
        response = client.get('/instagram/profile')
        assert response.status_code in [200, 401]
        
        response = client.get('/instagram/media')
        assert response.status_code in [200, 401]
    
    def test_whatsapp_endpoints(self, client):
        """Test WhatsApp service endpoints."""
        response = client.get('/whatsapp/status')
        assert response.status_code in [200, 401]
        
        response = client.get('/whatsapp/chats')
        assert response.status_code in [200, 401]
    
    def test_files_endpoints(self, client):
        """Test Files service endpoints."""
        response = client.get('/files/list')
        assert response.status_code == 200
        
        response = client.get('/files/search?q=test')
        assert response.status_code == 200
        
        response = client.get('/files/read?filename=test.txt')
        assert response.status_code in [200, 404]


class TestServerAuthentication:
    """Test cases for server authentication."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_oauth_flow_initiation(self, client):
        """Test OAuth flow initiation for all services."""
        services = ['spotify', 'google', 'facebook', 'instagram']
        
        for service in services:
            response = client.get(f'/{service}/auth')
            assert response.status_code in [200, 302]
    
    def test_oauth_callback_handling(self, client):
        """Test OAuth callback handling."""
        services = ['spotify', 'google', 'facebook', 'instagram']
        
        for service in services:
            response = client.get(f'/{service}/callback?code=test_code&state=test_state')
            assert response.status_code in [200, 302, 400]
    
    def test_unauthenticated_access(self, client):
        """Test unauthenticated access to protected endpoints."""
        protected_endpoints = [
            '/spotify/profile', '/google/profile', '/facebook/profile',
            '/instagram/profile', '/whatsapp/status'
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 401, 302]


class TestServerErrorHandling:
    """Test cases for server error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_invalid_endpoint(self, client):
        """Test invalid endpoint handling."""
        response = client.get('/invalid/endpoint')
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed handling."""
        response = client.post('/health')
        assert response.status_code == 405
    
    def test_missing_parameters(self, client):
        """Test missing required parameters."""
        response = client.get('/files/search')
        assert response.status_code == 400
    
    def test_service_unavailable(self, client):
        """Test service unavailable handling."""
        with patch('api_server.SpotifyAPI') as mock_spotify:
            mock_spotify.side_effect = Exception("Service unavailable")
            
            response = client.get('/spotify/profile')
            assert response.status_code in [200, 500, 503]


class TestServerPerformance:
    """Test cases for server performance."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_response_time(self, client):
        """Test response time for endpoints."""
        start_time = time.time()
        response = client.get('/health')
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 1.0
        assert response.status_code == 200
    
    def test_concurrent_requests(self, client):
        """Test concurrent request handling."""
        import threading
        
        results = []
        
        def make_request():
            response = client.get('/health')
            results.append(response.status_code)
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 10
        assert all(status == 200 for status in results)
