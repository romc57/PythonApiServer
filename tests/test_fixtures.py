"""Test fixtures and mock data."""
import json
import os
from pathlib import Path


class TestFixtures:
    """Test fixtures and mock data."""
    
    @staticmethod
    def create_mock_auth_files():
        """Create mock authentication files for testing."""
        auth_dir = Path("tests/fixtures/auth")
        auth_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock Spotify credentials
        spotify_creds = {
            "client_id": "test_spotify_client_id",
            "client_secret": "test_spotify_client_secret",
            "redirect_uri": "http://localhost:8081/spotify/callback"
        }
        
        with open(auth_dir / "spotify.json", "w") as f:
            json.dump(spotify_creds, f)
        
        # Mock Google credentials
        google_creds = {
            "client_id": "test_google_client_id",
            "client_secret": "test_google_client_secret",
            "redirect_uri": "http://localhost:8081/google/callback"
        }
        
        with open(auth_dir / "google.json", "w") as f:
            json.dump(google_creds, f)
        
        # Mock Facebook credentials
        facebook_creds = {
            "client_id": "test_facebook_client_id",
            "client_secret": "test_facebook_client_secret",
            "redirect_uri": "http://localhost:8081/facebook/callback"
        }
        
        with open(auth_dir / "facebook.json", "w") as f:
            json.dump(facebook_creds, f)
    
    @staticmethod
    def create_mock_local_data():
        """Create mock local data files for testing."""
        data_dir = Path("tests/fixtures/local-data")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        test_files = {
            "test-ai.txt": "Artificial intelligence is revolutionizing technology.",
            "test-blockchain.txt": "Blockchain technology enables secure transactions.",
            "test-climate.txt": "Climate change requires immediate global action."
        }
        
        for filename, content in test_files.items():
            with open(data_dir / filename, "w") as f:
                f.write(content)
    
    @staticmethod
    def get_mock_api_responses():
        """Get mock API responses for testing."""
        return {
            "spotify": {
                "profile": {
                    "id": "test_user",
                    "display_name": "Test User",
                    "email": "test@example.com",
                    "country": "US"
                },
                "currently_playing": {
                    "is_playing": True,
                    "item": {
                        "name": "Test Song",
                        "artists": [{"name": "Test Artist"}],
                        "album": {"name": "Test Album"}
                    }
                },
                "playlists": {
                    "items": [
                        {"name": "Test Playlist", "id": "playlist_1"},
                        {"name": "Another Playlist", "id": "playlist_2"}
                    ]
                }
            },
            "google": {
                "profile": {
                    "id": "test_google_user",
                    "name": "Test Google User",
                    "email": "test@gmail.com"
                },
                "drive_files": {
                    "files": [
                        {"name": "test_doc.pdf", "id": "file_1"},
                        {"name": "test_sheet.xlsx", "id": "file_2"}
                    ]
                }
            },
            "facebook": {
                "profile": {
                    "id": "test_facebook_user",
                    "name": "Test Facebook User"
                },
                "pages": {
                    "data": [
                        {"name": "Test Page", "id": "page_1"},
                        {"name": "Another Page", "id": "page_2"}
                    ]
                }
            },
            "whatsapp": {
                "status": {
                    "connected": True,
                    "ready": True,
                    "browser_status": "active"
                },
                "chats": [
                    "Test Chat 1",
                    "Test Chat 2",
                    "Test Chat 3"
                ]
            }
        }
    
    @staticmethod
    def cleanup_test_files():
        """Clean up test files after testing."""
        import shutil
        
        test_dirs = [
            "tests/fixtures",
            "tests/__pycache__",
            ".pytest_cache",
            "htmlcov",
            ".coverage"
        ]
        
        for dir_path in test_dirs:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
