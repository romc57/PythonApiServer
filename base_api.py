"""Base API class with all common functionality."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
import requests
import time
import json
import os
from pathlib import Path

class BaseAPI(ABC):
    """Base class for all API services with ALL common functionality."""
    
    def __init__(self, service_name: str, client_id: str, client_secret: str, 
                 redirect_uri: str, auth_url: str, token_url: str, api_base_url: str):
        """Initialize base API with all common components."""
        self.service_name = service_name
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_url = auth_url
        self.token_url = token_url
        self.api_base_url = api_base_url
        self.tokens_file = self._get_tokens_file_path()
        self._tokens = self._load_tokens()
        self.session = requests.Session()
        self._setup_session()
    
    def _get_tokens_file_path(self) -> Path:
        """Get path to tokens file."""
        current_dir = Path(__file__).parent
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
    
    def _setup_session(self) -> None:
        """Setup requests session with default headers."""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_auth_url(self) -> str:
        """Get OAuth authorization URL."""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.get_scopes()),
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        param_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{self.auth_url}?{param_string}"
    
    def handle_callback(self, code: str) -> bool:
        """Handle OAuth callback."""
        print(f"Handling callback for {self.service_name} with code: {code[:20]}...")
        print(f"Using redirect_uri: {self.redirect_uri}")
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        try:
            # Spotify token endpoint expects form-encoded data, not JSON
            # Use a fresh requests session without our JSON headers
            import requests
            response = requests.post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self._tokens.update({
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
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
            else:
                print("No response available")
            return False
        except Exception as e:
            print(f"Unexpected error exchanging code for tokens: {e}")
            print(f"Error type: {type(e)}")
            return False
    
    def _refresh_token(self) -> bool:
        """Refresh access token using refresh token."""
        refresh_token = self._tokens.get('refresh_token')
        if not refresh_token:
            return False
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = self.session.post(self.token_url, data=data, timeout=30)
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
    
    def get_access_token(self) -> Optional[str]:
        """Get current access token, refreshing if necessary."""
        if not self._tokens.get('access_token'):
            return None
        
        expires_at = self._tokens.get('expires_at', 0)
        if time.time() >= expires_at - 300:  # Refresh 5 minutes before expiry
            if not self._refresh_token():
                return None
        
        return self._tokens.get('access_token')
    
    def is_authenticated(self) -> bool:
        """Check if API is authenticated."""
        return bool(self.get_access_token())
    
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
        """Make authenticated request with retry logic."""
        url = f"{self.api_base_url}{endpoint}"
        headers = self._get_headers()
        
        for attempt in range(3):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=30,
                    **kwargs
                )
                
                if response.status_code == 401:
                    if self._refresh_token():
                        headers = self._get_headers()
                        continue
                    else:
                        raise Exception("Authentication failed and token refresh unsuccessful")
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 1))
                    time.sleep(retry_after)
                    continue
                
                if response.status_code >= 500:
                    if attempt < 2:
                        time.sleep(1 * (2 ** attempt))
                        continue
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout:
                if attempt < 2:
                    time.sleep(1 * (2 ** attempt))
                    continue
                raise Exception(f"Request timeout after 3 attempts")
            
            except requests.exceptions.ConnectionError:
                if attempt < 2:
                    time.sleep(1 * (2 ** attempt))
                    continue
                raise Exception(f"Connection error after 3 attempts")
            
            except requests.exceptions.RequestException as e:
                raise Exception(f"Request failed: {e}")
        
        raise Exception(f"Request failed after 3 attempts")
    
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
    
    def _load_credentials(self, service_name: str) -> Dict[str, str]:
        """Load service credentials."""
        try:
            with open(f'auth/{service_name}.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"{service_name.title()} credentials not found at auth/{service_name}.json")
    
    def _handle_success_response(self, response: requests.Response, expected_status: int = 204) -> Dict[str, Any]:
        """Handle success response with common pattern."""
        return {"success": response.status_code == expected_status}
    
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