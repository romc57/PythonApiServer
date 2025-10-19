"""Base Meta API class with shared authentication for Facebook, WhatsApp, and Instagram."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import requests
import time
import json
import os
from pathlib import Path

class BaseMetaAPI(ABC):
    """Base class for all Meta APIs (Facebook, WhatsApp, Instagram) with shared authentication."""
    
    def __init__(self, app_id: str, app_secret: str, service_name: str, api_version: str = "v18.0"):
        """Initialize Meta API with shared components."""
        self.app_id = app_id
        self.app_secret = app_secret
        self.service_name = service_name
        self.api_version = api_version
        self.tokens_file = self._get_tokens_file_path()
        self._tokens = self._load_tokens()
        self.session = requests.Session()
        self._setup_session()
        
        # Try to restore authentication on startup
        self._try_restore_authentication()
    
    def _get_tokens_file_path(self) -> Path:
        """Get path to tokens file."""
        current_dir = Path(__file__).parent.parent.parent
        return current_dir / 'auth' / f'{self.service_name}_tokens.json'
    
    def _load_tokens(self) -> Dict[str, Any]:
        """Load tokens from file."""
        try:
            if self.tokens_file.exists():
                with open(self.tokens_file, 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load tokens: {e}")
        return {}
    
    def _save_tokens(self) -> None:
        """Save tokens to file."""
        try:
            self.tokens_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tokens_file, 'w') as f:
                json.dump(self._tokens, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save tokens: {e}")
    
    def _try_restore_authentication(self) -> None:
        """Try to restore authentication on startup."""
        try:
            if not self._tokens:
                print(f"ℹ️ {self.service_name}: No saved tokens found")
                return
            
            # Check if we have an access token
            access_token = self._tokens.get('access_token')
            if not access_token:
                print(f"ℹ️ {self.service_name}: No access token found")
                return
            
            # Check if token is expired
            expires_at = self._tokens.get('expires_at', 0)
            current_time = time.time()
            
            if current_time >= expires_at - 300:  # Token expired or expires in 5 minutes
                print(f"🔄 {self.service_name}: Token expired, attempting refresh...")
                
                # Try to refresh the token
                if self._refresh_token():
                    print(f"✅ {self.service_name}: Token refreshed successfully!")
                else:
                    print(f"⚠️ {self.service_name}: Token refresh failed, need to re-authenticate")
                    # Clear invalid tokens
                    self._tokens = {}
                    self._save_tokens()
            else:
                print(f"✅ {self.service_name}: Valid token found, authentication restored!")
                
        except Exception as e:
            print(f"Warning: Could not restore {self.service_name} authentication: {e}")
            # Clear potentially corrupted tokens
            self._tokens = {}
            self._save_tokens()
    
    def _setup_session(self) -> None:
        """Setup requests session with default headers."""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_auth_url(self) -> str:
        """Get OAuth authorization URL for Meta APIs."""
        params = {
            'client_id': self.app_id,
            'redirect_uri': self.get_redirect_uri(),
            'scope': ','.join(self.get_scopes()),
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        param_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"https://www.facebook.com/{self.api_version}/dialog/oauth?{param_string}"
    
    def get_redirect_uri(self) -> str:
        """Get redirect URI for this service."""
        return f"http://localhost:8081/{self.service_name}/callback"
    
    def handle_callback(self, code: str) -> bool:
        """Handle OAuth callback for Meta APIs."""
        print(f"Handling callback for {self.service_name} with code: {code[:20]}...")
        
        data = {
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.get_redirect_uri()
        }
        
        try:
            response = requests.post(
                f'https://graph.facebook.com/{self.api_version}/oauth/access_token',
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._tokens.update({
                'access_token': token_data.get('access_token'),
                'expires_in': token_data.get('expires_in'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_at': time.time() + token_data.get('expires_in', 3600)
            })
            
            self._save_tokens()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Error exchanging code for tokens: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response content: {e.response.text}")
            return False
        except Exception as e:
            print(f"Unexpected error exchanging code for tokens: {e}")
            return False
    
    def get_access_token(self) -> Optional[str]:
        """Get current access token."""
        return self._tokens.get('access_token')
    
    def is_authenticated(self) -> bool:
        """Check if API is authenticated."""
        return bool(self.get_access_token())
    
    def _refresh_token(self) -> bool:
        """Refresh access token using refresh token."""
        refresh_token = self._tokens.get('refresh_token')
        if not refresh_token:
            return False
        
        data = {
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = self.session.post(
                f'https://graph.facebook.com/{self.api_version}/oauth/access_token',
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._tokens.update({
                'access_token': token_data.get('access_token'),
                'expires_in': token_data.get('expires_in'),
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_at': time.time() + token_data.get('expires_in', 3600)
            })
            
            self._save_tokens()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Error refreshing token: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with current access token."""
        access_token = self.get_access_token()
        if not access_token:
            raise Exception(f"No valid access token available for {self.service_name}")
        
        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated request to Meta Graph API."""
        url = f"https://graph.facebook.com/{self.api_version}{endpoint}"
        headers = self._get_headers()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def _handle_api_call(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Handle API call with common error handling."""
        try:
            response = self._make_request(method, endpoint, **kwargs)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def _get_request_param(self, param_name: str, default_value: Any = None, param_type: type = str) -> Any:
        """Get request parameter with common handling."""
        try:
            from flask import request
            value = request.args.get(param_name, default_value)
            if param_type == int and value is not None:
                return int(value)
            return value
        except (ValueError, TypeError):
            return default_value
    
    def _validate_required_param(self, param_name: str) -> str:
        """Validate required parameter."""
        try:
            from flask import request
            value = request.args.get(param_name) or (request.json.get(param_name) if request.is_json else None)
            if not value:
                raise ValueError(f"Missing required parameter: {param_name}")
            return str(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid parameter {param_name}: {e}")
    
    def _get_request_json(self) -> Dict[str, Any]:
        """Get request JSON data."""
        try:
            from flask import request
            return request.get_json() or {}
        except Exception:
            return {}
    
    def _get_service_urls(self) -> Dict[str, str]:
        """Get service-specific URLs."""
        return {
            "auth_url": f"/{self.service_name}/auth",
            "callback_url": f"/{self.service_name}/callback"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "service": self.service_name,
            "authenticated": self.is_authenticated(),
            "status": "ready" if self.is_authenticated() else "not_authenticated"
        }
    
    @abstractmethod
    def get_scopes(self) -> List[str]:
        """Get OAuth scopes for this service."""
        pass
    
    @abstractmethod
    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Get available endpoints for this API service."""
        pass
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information."""
        pass
