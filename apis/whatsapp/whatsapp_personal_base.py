"""WhatsApp Personal API base class following the existing API pattern."""
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from .whatsapp_personal_api import WhatsAppPersonalAPI
import json
import time

class WhatsAppPersonalBaseAPI:
    """WhatsApp Personal API base class following the existing pattern."""
    
    def __init__(self, config_path: str = 'auth/whatsapp_personal.json'):
        """Initialize WhatsApp Personal API."""
        self.service_name = 'whatsapp_personal'
        self.config_path = config_path
        self.config = self._load_config()
        self.whatsapp_api = WhatsAppPersonalAPI(
            session_data_path=self.config.get('session_data_path', 'auth/whatsapp_personal_session.json'),
            headless=self.config.get('headless', False),
            rate_limit_delay=self.config.get('rate_limit_delay', 1.0),
            max_retries=self.config.get('max_retries', 3)
        )
        self.limits = {
            'max_contacts': self.config.get('max_contacts', 100),
            'max_conversations': self.config.get('max_conversations', 50),
            'max_messages': self.config.get('max_messages', 100)
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_path} not found, using defaults")
            return {}
    
    def get_scopes(self) -> List[str]:
        """Get scopes for WhatsApp Personal API."""
        return ['whatsapp_personal_messaging', 'whatsapp_personal_contacts']
    
    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Get WhatsApp Personal API endpoints."""
        return {
            "start-session": {
                "method": "POST",
                "description": "Start WhatsApp Web session",
                "handler": self.start_session
            },
            "start-session-form": {
                "method": "GET",
                "description": "Show start session form",
                "handler": self.start_session_form
            },
            "close-session": {
                "method": "POST",
                "description": "Close WhatsApp Web session",
                "handler": self.close_session
            },
            "contacts": {
                "method": "GET",
                "description": "Get WhatsApp contacts",
                "handler": self.get_contacts,
                "params": ["limit"]
            },
            "conversations": {
                "method": "GET",
                "description": "Get WhatsApp conversations",
                "handler": self.get_conversations,
                "params": ["limit"]
            },
            "search": {
                "method": "GET",
                "description": "Search conversations",
                "handler": self.search_conversation,
                "params": ["query"]
            },
            "messages": {
                "method": "GET",
                "description": "Get messages from current chat",
                "handler": self.get_messages,
                "params": ["limit"]
            },
            "send-message": {
                "method": "POST",
                "description": "Send message to contact",
                "handler": self.send_message,
                "params": ["contact", "message"]
            },
            "status": {
                "method": "GET",
                "description": "Get API status",
                "handler": self.get_status
            }
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get WhatsApp Personal service information."""
        return {
            "name": "WhatsApp Personal",
            "description": "WhatsApp Personal API using web scraping",
            "icon": "📱",
            "color": "#25d366",
            "auth_url": "/whatsapp_personal/start-session",
            "callback_url": "/whatsapp_personal/start-session"
        }
    
    def is_authenticated(self) -> bool:
        """Check if WhatsApp session is authenticated."""
        return self.whatsapp_api.is_authenticated
    
    def get_access_token(self) -> str:
        """Get access token (not applicable for personal API)."""
        return "personal_session" if self.is_authenticated() else None
    
    def _validate_limit_param(self, param_name: str, max_value: int) -> int:
        """Validate limit parameter."""
        try:
            from flask import request
            value = request.args.get(param_name, max_value)
            limit = int(value) if value else max_value
            return min(limit, max_value)
        except (ValueError, TypeError):
            return max_value
    
    def _validate_required_param(self, param_name: str) -> str:
        """Validate required parameter."""
        try:
            from flask import request
            value = request.args.get(param_name) or request.json.get(param_name) if request.is_json else None
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
    
    # API Methods
    def start_session(self) -> Dict[str, Any]:
        """Start WhatsApp Web session."""
        try:
            result = self.whatsapp_api.start_session()
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def start_session_form(self) -> str:
        """Show start session form."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WhatsApp Personal API - Start Session</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                .container { background: #f8f9fa; padding: 30px; border-radius: 10px; }
                .button { background: #25d366; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 8px 5px; }
                .button:hover { background: #1ea952; }
                .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .warning { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📱 WhatsApp Personal API</h1>
                <p>Start a WhatsApp Web session to access your personal WhatsApp data.</p>
                
                <div class="info">
                    <h3>ℹ️ How it works:</h3>
                    <ol>
                        <li>Click "Start Session" below</li>
                        <li>A browser window will open with WhatsApp Web</li>
                        <li>Scan the QR code with your phone</li>
                        <li>Once authenticated, you can use all API endpoints</li>
                    </ol>
                </div>
                
                <div class="warning">
                    <h3>⚠️ Docker Limitation:</h3>
                    <p><strong>If you see a Chrome WebDriver error, this is expected in Docker!</strong></p>
                    <p>WhatsApp Personal API requires a display to show the browser window. Docker containers don't have displays by default.</p>
                    <p><strong>To use WhatsApp Personal API:</strong></p>
                    <ol>
                        <li>Stop Docker: <code>docker compose down</code></li>
                        <li>Run locally: <code>python api_server.py</code></li>
                        <li>Access: <code>http://localhost:8081/whatsapp/auth</code></li>
                    </ol>
                </div>
                
                <form action="/whatsapp_personal/start-session" method="POST" style="text-align: center;">
                    <button type="submit" class="button">🚀 Start WhatsApp Session</button>
                </form>
                
                <div style="text-align: center; margin-top: 20px;">
                    <a href="/" class="button">← Back to Dashboard</a>
                    <a href="/whatsapp_personal/status" class="button">📊 Check Status</a>
                </div>
            </div>
        </body>
        </html>
        """
    
    def close_session(self) -> Dict[str, Any]:
        """Close WhatsApp Web session."""
        try:
            result = self.whatsapp_api.close_session()
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_contacts(self) -> Dict[str, Any]:
        """Get WhatsApp contacts."""
        if not self.is_authenticated():
            return {"error": "Not authenticated. Please start session first."}
        
        limit = self._validate_limit_param('limit', self.limits['max_contacts'])
        
        try:
            result = self.whatsapp_api.get_contacts(limit=limit)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_conversations(self) -> Dict[str, Any]:
        """Get WhatsApp conversations."""
        if not self.is_authenticated():
            return {"error": "Not authenticated. Please start session first."}
        
        limit = self._validate_limit_param('limit', self.limits['max_conversations'])
        
        try:
            result = self.whatsapp_api.get_conversations(limit=limit)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_conversation(self) -> Dict[str, Any]:
        """Search conversations."""
        if not self.is_authenticated():
            return {"error": "Not authenticated. Please start session first."}
        
        query = self._validate_required_param('query')
        
        try:
            result = self.whatsapp_api.search_conversation(query)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_messages(self) -> Dict[str, Any]:
        """Get messages from current chat."""
        if not self.is_authenticated():
            return {"error": "Not authenticated. Please start session first."}
        
        limit = self._validate_limit_param('limit', self.limits['max_messages'])
        
        try:
            result = self.whatsapp_api.get_messages_from_current_chat(limit=limit)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_message(self) -> Dict[str, Any]:
        """Send message to contact."""
        if not self.is_authenticated():
            return {"error": "Not authenticated. Please start session first."}
        
        contact = self._validate_required_param('contact')
        message = self._validate_required_param('message')
        
        try:
            result = self.whatsapp_api.send_message(contact, message)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get API status."""
        return self.whatsapp_api.get_status()
    
    # Methods required by Flask app but not applicable to WhatsApp Personal API
    def get_auth_url(self) -> str:
        """Get auth URL - not applicable for WhatsApp Personal API."""
        return "/whatsapp_personal/start-session"
    
    def handle_callback(self, code: str) -> bool:
        """Handle callback - not applicable for WhatsApp Personal API."""
        return False
    
    def get_access_token(self) -> str:
        """Get access token - not applicable for WhatsApp Personal API."""
        return "personal_session" if self.is_authenticated() else None
