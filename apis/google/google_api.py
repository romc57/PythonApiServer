"""Google API implementation with only unique logic."""
from typing import Dict, Any, List
from base_api import BaseAPI
import json

class GoogleAPI(BaseAPI):
    """Google API service implementation with only unique logic."""
    
    def __init__(self):
        """Initialize Google API service."""
        credentials = self._load_credentials('google')
        super().__init__(
            service_name='google',
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret'],
            redirect_uri=credentials['redirect_uri'],
            auth_url='https://accounts.google.com/o/oauth2/v2/auth',
            token_url='https://oauth2.googleapis.com/token',
            api_base_url='https://www.googleapis.com'
        )
    
    def get_scopes(self) -> List[str]:
        """Get Google OAuth scopes."""
        return [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/youtube.readonly'
        ]
    
    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Get Google API endpoints."""
        return {
            "gmail/profile": {
                "method": "GET",
                "description": "Get Gmail profile",
                "handler": self.get_gmail_profile
            },
            "gmail/messages": {
                "method": "GET",
                "description": "List Gmail messages",
                "handler": self.get_gmail_messages
            },
            "drive/files": {
                "method": "GET",
                "description": "List Drive files",
                "handler": self.get_drive_files
            },
            "calendar/events": {
                "method": "GET",
                "description": "List Calendar events",
                "handler": self.get_calendar_events
            },
            "youtube/search": {
                "method": "GET",
                "description": "Search YouTube videos",
                "handler": self.search_youtube,
                "params": ["q"]
            }
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get Google service information."""
        service_urls = self._get_service_urls()
        return {
            "name": "Google",
            "description": "Gmail, Drive, Calendar, and YouTube",
            "icon": "🔍",
            "color": "#4285f4",
            **service_urls
        }
    
    # Google-specific methods (only unique logic)
    def get_gmail_profile(self) -> Dict[str, Any]:
        """Get Gmail profile."""
        return self._handle_api_call('GET', '/gmail/v1/users/me/profile')
    
    def get_gmail_messages(self) -> Dict[str, Any]:
        """Get Gmail messages."""
        query = self._get_request_param('q', '')
        max_results = self._get_request_param('max_results', 10, int)
        return self._handle_api_call('GET', f'/gmail/v1/users/me/messages?q={query}&maxResults={max_results}')
    
    def get_drive_files(self) -> Dict[str, Any]:
        """Get Drive files."""
        page_size = self._get_request_param('page_size', 10, int)
        query = self._get_request_param('q')
        url = f'/drive/v3/files?pageSize={page_size}'
        if query:
            url += f'&q={query}'
        return self._handle_api_call('GET', url)
    
    def get_calendar_events(self) -> Dict[str, Any]:
        """Get Calendar events."""
        max_results = self._get_request_param('max_results', 10, int)
        return self._handle_api_call('GET', f'/calendar/v3/calendars/primary/events?maxResults={max_results}')
    
    def search_youtube(self) -> Dict[str, Any]:
        """Search YouTube."""
        query = self._validate_required_param('q')
        max_results = self._get_request_param('max_results', 10, int)
        return self._handle_api_call('GET', f'/youtube/v3/search?part=snippet&q={query}&maxResults={max_results}')