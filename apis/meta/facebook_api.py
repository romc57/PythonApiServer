"""Facebook Graph API implementation with all free endpoints."""
from typing import Dict, Any, List
from .base_meta_api import BaseMetaAPI

class FacebookAPI(BaseMetaAPI):
    """Facebook Graph API service implementation."""
    
    def __init__(self, app_id: str, app_secret: str):
        """Initialize Facebook Graph API service."""
        super().__init__(app_id, app_secret, 'facebook')
    
    def get_scopes(self) -> List[str]:
        """Get Facebook Graph API OAuth scopes."""
        return [
            'public_profile',
            'email',
            'user_posts',
            'user_photos',
            'user_videos',
            'user_friends'
        ]
    
    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Get Facebook Graph API endpoints."""
        return {
            "profile": {
                "method": "GET",
                "description": "Get user profile information",
                "handler": self.get_profile
            },
            "posts": {
                "method": "GET",
                "description": "Get user's posts",
                "handler": self.get_posts
            },
            "photos": {
                "method": "GET",
                "description": "Get user's photos",
                "handler": self.get_photos
            },
            "videos": {
                "method": "GET",
                "description": "Get user's videos",
                "handler": self.get_videos
            },
            "pages": {
                "method": "GET",
                "description": "Get user's Facebook pages",
                "handler": self.get_pages
            },
            "page-posts": {
                "method": "GET",
                "description": "Get posts from a specific page",
                "handler": self.get_page_posts,
                "params": {
                    "page_id": "Required: Facebook page ID"
                }
            },
            "create-post": {
                "method": "POST",
                "description": "Create a new post",
                "handler": self.create_post,
                "params": {
                    "message": "Required: Post content"
                }
            },
            "create-photo": {
                "method": "POST",
                "description": "Upload a photo",
                "handler": self.create_photo,
                "params": {
                    "url": "Required: Photo URL",
                    "message": "Optional: Photo caption"
                }
            },
            "groups": {
                "method": "GET",
                "description": "Get user's groups",
                "handler": self.get_groups
            },
            "events": {
                "method": "GET",
                "description": "Get user's events",
                "handler": self.get_events
            },
            "friends": {
                "method": "GET",
                "description": "Get user's friends",
                "handler": self.get_friends
            },
            "feed": {
                "method": "GET",
                "description": "Get user's news feed",
                "handler": self.get_feed
            },
            "likes": {
                "method": "GET",
                "description": "Get user's likes",
                "handler": self.get_likes
            },
            "albums": {
                "method": "GET",
                "description": "Get user's photo albums",
                "handler": self.get_albums
            },
            "album-photos": {
                "method": "GET",
                "description": "Get photos from an album",
                "handler": self.get_album_photos,
                "params": {
                    "album_id": "Required: Facebook album ID"
                }
            }
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get Facebook service information."""
        service_urls = self._get_service_urls()
        return {
            "name": "Facebook",
            "description": "Social media platform and Graph API",
            "icon": "📘",
            "color": "#1877f2",
            **service_urls
        }
    
    # Facebook-specific methods
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        fields = "id,name,email,picture,cover,about,bio,location,website,birthday,gender"
        return self._handle_api_call('GET', f'/me?fields={fields}')
    
    def get_posts(self) -> Dict[str, Any]:
        """Get user's posts."""
        limit = self._get_request_param('limit', 25, int)
        return self._handle_api_call('GET', f'/me/posts?limit={limit}')
    
    def get_photos(self) -> Dict[str, Any]:
        """Get user's photos."""
        limit = self._get_request_param('limit', 25, int)
        return self._handle_api_call('GET', f'/me/photos?limit={limit}')
    
    def get_videos(self) -> Dict[str, Any]:
        """Get user's videos."""
        limit = self._get_request_param('limit', 25, int)
        return self._handle_api_call('GET', f'/me/videos?limit={limit}')
    
    def get_pages(self) -> Dict[str, Any]:
        """Get user's Facebook pages."""
        return self._handle_api_call('GET', '/me/accounts')
    
    def get_page_posts(self) -> Dict[str, Any]:
        """Get posts from a specific page."""
        page_id = self._validate_required_param('page_id')
        limit = self._get_request_param('limit', 25, int)
        return self._handle_api_call('GET', f'/{page_id}/posts?limit={limit}')
    
    def create_post(self) -> Dict[str, Any]:
        """Create a new post."""
        message = self._validate_required_param('message')
        page_id = self._get_request_json().get('page_id')
        
        if page_id:
            # Post to a specific page
            return self._handle_api_call('POST', f'/{page_id}/feed', 
                                       json={'message': message})
        else:
            # Post to user's timeline
            return self._handle_api_call('POST', '/me/feed', 
                                       json={'message': message})
    
    def create_photo(self) -> Dict[str, Any]:
        """Upload a photo."""
        url = self._validate_required_param('url')
        message = self._get_request_json().get('message', '')
        page_id = self._get_request_json().get('page_id')
        
        data = {
            'url': url,
            'message': message
        }
        
        if page_id:
            # Upload to a specific page
            return self._handle_api_call('POST', f'/{page_id}/photos', json=data)
        else:
            # Upload to user's photos
            return self._handle_api_call('POST', '/me/photos', json=data)
    
    def get_groups(self) -> Dict[str, Any]:
        """Get user's groups."""
        return self._handle_api_call('GET', '/me/groups')
    
    def get_events(self) -> Dict[str, Any]:
        """Get user's events."""
        limit = self._get_request_param('limit', 25, int)
        return self._handle_api_call('GET', f'/me/events?limit={limit}')
    
    def get_friends(self) -> Dict[str, Any]:
        """Get user's friends."""
        limit = self._get_request_param('limit', 25, int)
        return self._handle_api_call('GET', f'/me/friends?limit={limit}')
    
    def get_feed(self) -> Dict[str, Any]:
        """Get user's news feed."""
        limit = self._get_request_param('limit', 25, int)
        return self._handle_api_call('GET', f'/me/feed?limit={limit}')
    
    def get_likes(self) -> Dict[str, Any]:
        """Get user's likes."""
        limit = self._get_request_param('limit', 25, int)
        return self._handle_api_call('GET', f'/me/likes?limit={limit}')
    
    def get_albums(self) -> Dict[str, Any]:
        """Get user's photo albums."""
        return self._handle_api_call('GET', '/me/albums')
    
    def get_album_photos(self) -> Dict[str, Any]:
        """Get photos from an album."""
        album_id = self._validate_required_param('album_id')
        limit = self._get_request_param('limit', 25, int)
        return self._handle_api_call('GET', f'/{album_id}/photos?limit={limit}')
    
    def get_page_info(self, page_id: str) -> Dict[str, Any]:
        """Get detailed information about a page."""
        fields = "id,name,about,description,website,phone,emails,location,hours,cover,picture"
        return self._handle_api_call('GET', f'/{page_id}?fields={fields}')
    
    def get_page_insights(self, page_id: str) -> Dict[str, Any]:
        """Get page insights and analytics."""
        return self._handle_api_call('GET', f'/{page_id}/insights')
    
    def create_event(self, name: str, start_time: str, description: str = "") -> Dict[str, Any]:
        """Create a new event."""
        data = {
            'name': name,
            'start_time': start_time,
            'description': description
        }
        return self._handle_api_call('POST', '/me/events', json=data)
    
    def get_user_posts_by_date(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get user's posts within a date range."""
        return self._handle_api_call('GET', f'/me/posts?since={start_date}&until={end_date}')
    
    def search_posts(self, query: str) -> Dict[str, Any]:
        """Search for posts containing specific text."""
        return self._handle_api_call('GET', f'/me/posts?q={query}')
