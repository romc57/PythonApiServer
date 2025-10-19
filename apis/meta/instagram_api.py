"""Instagram Basic Display API implementation with all free endpoints."""
from typing import Dict, Any, List
from .base_meta_api import BaseMetaAPI

class InstagramAPI(BaseMetaAPI):
    """Instagram Basic Display API service implementation."""
    
    def __init__(self, app_id: str, app_secret: str):
        """Initialize Instagram Basic Display API service."""
        super().__init__(app_id, app_secret, 'instagram')
    
    def get_scopes(self) -> List[str]:
        """Get Instagram Basic Display API OAuth scopes."""
        return [
            'user_profile',
            'user_media'
        ]
    
    def get_auth_url(self) -> str:
        """Get OAuth authorization URL for Instagram Basic Display API."""
        params = {
            'client_id': self.app_id,
            'redirect_uri': self.get_redirect_uri(),
            'scope': ','.join(self.get_scopes()),
            'response_type': 'code'
        }
        param_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"https://api.instagram.com/oauth/authorize?{param_string}"
    
    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Get Instagram Basic Display API endpoints."""
        return {
            "profile": {
                "method": "GET",
                "description": "Get user profile information",
                "handler": self.get_profile
            },
            "media": {
                "method": "GET",
                "description": "Get user's media (photos and videos)",
                "handler": self.get_media
            },
            "media-details": {
                "method": "GET",
                "description": "Get details of a specific media",
                "handler": self.get_media_details,
                "params": {
                    "media_id": "Required: Instagram media ID"
                }
            },
            "media-children": {
                "method": "GET",
                "description": "Get children of a media (for carousel posts)",
                "handler": self.get_media_children,
                "params": {
                    "media_id": "Required: Instagram media ID"
                }
            },
            "long-lived-token": {
                "method": "POST",
                "description": "Exchange short-lived token for long-lived token",
                "handler": self.get_long_lived_token
            },
            "refresh-token": {
                "method": "POST",
                "description": "Refresh long-lived token",
                "handler": self.refresh_long_lived_token
            },
            "hashtag-media": {
                "method": "GET",
                "description": "Get media by hashtag",
                "handler": self.get_hashtag_media,
                "params": {
                    "hashtag": "Required: Hashtag name (without #)"
                }
            },
            "user-media-by-date": {
                "method": "GET",
                "description": "Get user media by date range",
                "handler": self.get_media_by_date,
                "params": {
                    "since": "Required: Start date (YYYY-MM-DD)",
                    "until": "Required: End date (YYYY-MM-DD)"
                }
            },
            "media-insights": {
                "method": "GET",
                "description": "Get media insights (if available)",
                "handler": self.get_media_insights,
                "params": {
                    "media_id": "Required: Instagram media ID"
                }
            }
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get Instagram service information."""
        service_urls = self._get_service_urls()
        return {
            "name": "Instagram",
            "description": "Instagram Basic Display API for photos and videos",
            "icon": "📷",
            "color": "#E4405F",
            **service_urls
        }
    
    # Instagram-specific methods
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        fields = "id,username,account_type,media_count"
        return self._handle_api_call('GET', f'/me?fields={fields}')
    
    def get_media(self) -> Dict[str, Any]:
        """Get user's media (photos and videos)."""
        limit = self._get_request_param('limit', 25, int)
        fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
        return self._handle_api_call('GET', f'/me/media?fields={fields}&limit={limit}')
    
    def get_media_details(self) -> Dict[str, Any]:
        """Get details of a specific media."""
        media_id = self._validate_required_param('media_id')
        fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,children"
        return self._handle_api_call('GET', f'/{media_id}?fields={fields}')
    
    def get_media_children(self) -> Dict[str, Any]:
        """Get children of a media (for carousel posts)."""
        media_id = self._validate_required_param('media_id')
        fields = "id,media_type,media_url,thumbnail_url"
        return self._handle_api_call('GET', f'/{media_id}/children?fields={fields}')
    
    def get_long_lived_token(self) -> Dict[str, Any]:
        """Exchange short-lived token for long-lived token."""
        try:
            response = requests.get(
                f'https://graph.facebook.com/{self.api_version}/oauth/access_token',
                params={
                    'grant_type': 'ig_exchange_token',
                    'client_secret': self.app_secret,
                    'access_token': self.get_access_token()
                }
            )
            response.raise_for_status()
            token_data = response.json()
            
            # Update tokens with long-lived token
            self._tokens.update({
                'access_token': token_data.get('access_token'),
                'expires_in': token_data.get('expires_in'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_at': time.time() + token_data.get('expires_in', 3600)
            })
            self._save_tokens()
            
            return token_data
        except Exception as e:
            return {"error": str(e)}
    
    def refresh_long_lived_token(self) -> Dict[str, Any]:
        """Refresh long-lived token."""
        try:
            response = requests.get(
                f'https://graph.facebook.com/{self.api_version}/refresh_access_token',
                params={
                    'grant_type': 'ig_refresh_token',
                    'access_token': self.get_access_token()
                }
            )
            response.raise_for_status()
            token_data = response.json()
            
            # Update tokens with refreshed token
            self._tokens.update({
                'access_token': token_data.get('access_token'),
                'expires_in': token_data.get('expires_in'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_at': time.time() + token_data.get('expires_in', 3600)
            })
            self._save_tokens()
            
            return token_data
        except Exception as e:
            return {"error": str(e)}
    
    def get_hashtag_media(self) -> Dict[str, Any]:
        """Get media by hashtag."""
        hashtag = self._validate_required_param('hashtag')
        limit = self._get_request_param('limit', 25, int)
        fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
        
        # First get hashtag ID
        hashtag_response = self._handle_api_call('GET', f'/ig_hashtag_search?user_id=me&q={hashtag}')
        if 'error' in hashtag_response:
            return hashtag_response
        
        hashtag_id = hashtag_response['data'][0]['id']
        return self._handle_api_call('GET', f'/{hashtag_id}/recent_media?fields={fields}&limit={limit}')
    
    def get_media_by_date(self) -> Dict[str, Any]:
        """Get user media by date range."""
        since = self._validate_required_param('since')
        until = self._validate_required_param('until')
        fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
        
        return self._handle_api_call('GET', f'/me/media?fields={fields}&since={since}&until={until}')
    
    def get_media_insights(self) -> Dict[str, Any]:
        """Get media insights (if available)."""
        media_id = self._validate_required_param('media_id')
        metrics = "impressions,reach,engagement,likes,comments,shares,saves"
        
        return self._handle_api_call('GET', f'/{media_id}/insights?metric={metrics}')
    
    def get_user_stories(self) -> Dict[str, Any]:
        """Get user's stories."""
        fields = "id,media_type,media_url,thumbnail_url,permalink,timestamp"
        return self._handle_api_call('GET', f'/me/stories?fields={fields}')
    
    def get_media_comments(self, media_id: str) -> Dict[str, Any]:
        """Get comments for a specific media."""
        fields = "id,text,from,timestamp"
        return self._handle_api_call('GET', f'/{media_id}/comments?fields={fields}')
    
    def get_user_mentions(self) -> Dict[str, Any]:
        """Get media where user is mentioned."""
        fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
        return self._handle_api_call('GET', f'/me/mentioned_media?fields={fields}')
    
    def search_media(self, query: str) -> Dict[str, Any]:
        """Search for media by caption text."""
        fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
        return self._handle_api_call('GET', f'/me/media?fields={fields}&q={query}')
    
    def get_media_by_type(self, media_type: str) -> Dict[str, Any]:
        """Get media filtered by type (IMAGE, VIDEO, CAROUSEL_ALBUM)."""
        fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
        return self._handle_api_call('GET', f'/me/media?fields={fields}&media_type={media_type}')
    
    def get_user_albums(self) -> Dict[str, Any]:
        """Get user's albums (carousel posts)."""
        fields = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,children"
        return self._handle_api_call('GET', f'/me/media?fields={fields}&media_type=CAROUSEL_ALBUM')
