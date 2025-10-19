"""Spotify API implementation with only unique logic."""
from typing import Dict, Any, List
from base_api import BaseAPI
import json

class SpotifyAPI(BaseAPI):
    """Spotify API service implementation with only unique logic."""
    
    def __init__(self):
        """Initialize Spotify API service."""
        credentials = self._load_credentials('spotify')
        super().__init__(
            service_name='spotify',
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret'],
            redirect_uri=credentials['redirect_uri'],
            auth_url='https://accounts.spotify.com/authorize',
            token_url='https://accounts.spotify.com/api/token',
            api_base_url='https://api.spotify.com/v1'
        )
    
    def get_scopes(self) -> List[str]:
        """Get Spotify OAuth scopes."""
        return [
            'user-read-private',
            'user-read-email',
            'user-read-playback-state',
            'user-modify-playback-state',
            'user-read-currently-playing',
            'playlist-read-private',
            'playlist-read-collaborative',
            'user-library-read',
            'user-top-read',
            'user-read-recently-played'
        ]
    
    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Get Spotify API endpoints."""
        return {
            "profile": {
                "method": "GET",
                "description": "Get user profile",
                "handler": self.get_profile
            },
            "playlists": {
                "method": "GET", 
                "description": "List user playlists",
                "handler": self.get_playlists
            },
            "currently-playing": {
                "method": "GET",
                "description": "Get currently playing track",
                "handler": self.get_currently_playing
            },
            "search": {
                "method": "GET",
                "description": "Search music",
                "handler": self.search,
                "params": {
                    "q": "Required: Search query (artist, track, album name)"
                }
            },
            "playback/next": {
                "method": "POST",
                "description": "Skip to next track",
                "handler": self.skip_next
            },
            "playback/pause": {
                "method": "POST",
                "description": "Pause playback",
                "handler": self.pause
            },
            "playback/resume": {
                "method": "POST",
                "description": "Resume playback",
                "handler": self.resume
            }
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get Spotify service information."""
        service_urls = self._get_service_urls()
        return {
            "name": "Spotify",
            "description": "Music streaming and playback control",
            "icon": "🎵",
            "color": "#1db954",
            **service_urls
        }
    
    # Spotify-specific methods (only unique logic)
    def get_profile(self) -> Dict[str, Any]:
        """Get Spotify user profile."""
        return self._handle_api_call('GET', '/me')
    
    def get_playlists(self) -> Dict[str, Any]:
        """Get Spotify playlists."""
        limit = self._get_request_param('limit', 10, int)
        return self._handle_api_call('GET', f'/me/playlists?limit={limit}')
    
    def get_currently_playing(self) -> Dict[str, Any]:
        """Get currently playing track."""
        try:
            response = self._make_request('GET', '/me/player/currently-playing')
            if response.status_code == 204:
                return {"message": "No track currently playing"}
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def search(self) -> Dict[str, Any]:
        """Search Spotify."""
        query = self._validate_required_param('q')
        return self._handle_api_call('GET', f'/search?q={query}&type=track,artist,album&limit=20')
    
    def skip_next(self) -> Dict[str, Any]:
        """Skip to next track."""
        try:
            response = self._make_request('POST', '/me/player/next')
            return self._handle_success_response(response)
        except Exception as e:
            return {"error": str(e)}
    
    def pause(self) -> Dict[str, Any]:
        """Pause playback."""
        try:
            response = self._make_request('PUT', '/me/player/pause')
            return self._handle_success_response(response)
        except Exception as e:
            return {"error": str(e)}
    
    def resume(self) -> Dict[str, Any]:
        """Resume playback."""
        try:
            response = self._make_request('PUT', '/me/player/play')
            return self._handle_success_response(response)
        except Exception as e:
            return {"error": str(e)}