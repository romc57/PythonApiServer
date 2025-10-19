"""Unit tests for all service APIs."""
import pytest
from unittest.mock import patch, Mock
from tests.conftest import TestConfig, create_mock_credentials


class TestSpotifyAPI:
    """Unit tests for Spotify API."""
    
    @pytest.fixture
    def spotify_api(self):
        """Create Spotify API instance for testing."""
        with patch('apis.spotify.spotify_api.SpotifyAPI._load_credentials', return_value=create_mock_credentials('spotify')):
            from apis.spotify.spotify_api import SpotifyAPI
            return SpotifyAPI()
    
    def test_initialization(self, spotify_api):
        """Test Spotify API initialization."""
        assert spotify_api.service_name == 'spotify'
        assert spotify_api.api_base_url == 'https://api.spotify.com/v1'
    
    def test_get_scopes(self, spotify_api):
        """Test Spotify OAuth scopes."""
        scopes = spotify_api.get_scopes()
        expected_scopes = [
            'user-read-private', 'user-read-email', 'user-read-playback-state',
            'user-modify-playback-state', 'user-read-currently-playing'
        ]
        assert all(scope in scopes for scope in expected_scopes)
    
    @patch('apis.spotify.spotify_api.SpotifyAPI._handle_api_call')
    def test_get_profile(self, mock_handle_call, spotify_api):
        """Test get user profile."""
        mock_response = TestConfig.MOCK_SPOTIFY_RESPONSES['profile']
        mock_handle_call.return_value = mock_response
        
        result = spotify_api.get_profile()
        mock_handle_call.assert_called_once_with('GET', '/me')
        assert result == mock_response


class TestGoogleAPI:
    """Unit tests for Google API."""
    
    @pytest.fixture
    def google_api(self):
        """Create Google API instance for testing."""
        with patch('apis.google.google_api.GoogleAPI._load_credentials', return_value=create_mock_credentials('google')):
            from apis.google.google_api import GoogleAPI
            return GoogleAPI()
    
    def test_initialization(self, google_api):
        """Test Google API initialization."""
        assert google_api.service_name == 'google'
        assert google_api.api_base_url == 'https://www.googleapis.com/oauth2/v2'
    
    def test_get_scopes(self, google_api):
        """Test Google OAuth scopes."""
        scopes = google_api.get_scopes()
        expected_scopes = [
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email'
        ]
        assert all(scope in scopes for scope in expected_scopes)


class TestFacebookAPI:
    """Unit tests for Facebook API."""
    
    @pytest.fixture
    def facebook_api(self):
        """Create Facebook API instance for testing."""
        with patch('apis.meta.facebook_api.FacebookAPI._load_credentials', return_value=create_mock_credentials('facebook')):
            from apis.meta.facebook_api import FacebookAPI
            return FacebookAPI()
    
    def test_initialization(self, facebook_api):
        """Test Facebook API initialization."""
        assert facebook_api.service_name == 'facebook'
        assert facebook_api.api_base_url == 'https://graph.facebook.com/v18.0'
    
    def test_get_scopes(self, facebook_api):
        """Test Facebook OAuth scopes."""
        scopes = facebook_api.get_scopes()
        expected_scopes = ['public_profile', 'email']
        assert all(scope in scopes for scope in expected_scopes)


class TestInstagramAPI:
    """Unit tests for Instagram API."""
    
    @pytest.fixture
    def instagram_api(self):
        """Create Instagram API instance for testing."""
        with patch('apis.meta.instagram_api.InstagramAPI._load_credentials', return_value=create_mock_credentials('instagram')):
            from apis.meta.instagram_api import InstagramAPI
            return InstagramAPI()
    
    def test_initialization(self, instagram_api):
        """Test Instagram API initialization."""
        assert instagram_api.service_name == 'instagram'
        assert instagram_api.api_base_url == 'https://graph.facebook.com/v18.0'
    
    def test_get_scopes(self, instagram_api):
        """Test Instagram OAuth scopes."""
        scopes = instagram_api.get_scopes()
        expected_scopes = ['instagram_basic', 'instagram_content_publish']
        assert all(scope in scopes for scope in expected_scopes)


class TestWhatsAppAPI:
    """Unit tests for WhatsApp API."""
    
    @pytest.fixture
    def whatsapp_api(self):
        """Create WhatsApp API instance for testing."""
        with patch('apis.whatsapp.whatsapp_server_api.WhatsAppServerAPI._load_credentials', return_value=create_mock_credentials('whatsapp')):
            from apis.whatsapp.whatsapp_server_api import WhatsAppServerAPI
            return WhatsAppServerAPI()
    
    def test_initialization(self, whatsapp_api):
        """Test WhatsApp API initialization."""
        assert whatsapp_api.service_name == 'whatsapp'
    
    def test_get_endpoints(self, whatsapp_api):
        """Test WhatsApp API endpoints configuration."""
        endpoints = whatsapp_api.get_endpoints()
        assert 'status' in endpoints
        assert 'chats' in endpoints
        assert 'send-message' in endpoints


class TestFilesAPI:
    """Unit tests for Files API."""
    
    @pytest.fixture
    def files_api(self):
        """Create Files API instance for testing."""
        from apis.files.files_api import FilesAPI
        return FilesAPI()
    
    def test_initialization(self, files_api):
        """Test Files API initialization."""
        assert files_api.service_name == 'files'
        assert files_api.local_data_dir == 'local-data'
    
    def test_get_endpoints(self, files_api):
        """Test Files API endpoints configuration."""
        endpoints = files_api.get_endpoints()
        assert 'list' in endpoints
        assert 'read' in endpoints
        assert 'search' in endpoints
    
    @patch('apis.files.files_api.os.listdir')
    def test_list_files_success(self, mock_listdir, files_api):
        """Test list files - success."""
        mock_listdir.return_value = ['file1.txt', 'file2.txt']
        
        result = files_api.list_files()
        
        mock_listdir.assert_called_once_with('local-data')
        assert result['success'] is True
        assert 'files' in result
        assert len(result['files']) == 2
