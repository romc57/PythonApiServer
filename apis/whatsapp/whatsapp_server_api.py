"""WhatsApp Server API - Only endpoints, no scraping logic."""

import json
import sys
import os
from typing import Dict, Any, List
from flask import request

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .whatsapp_scraper import WhatsAppScraper


class WhatsAppServerAPI:
    """WhatsApp Server API - Clean endpoints only."""
    
    def __init__(self, config_path: str = 'auth/whatsapp/whatsapp_personal.json'):
        """Initialize WhatsApp Server API."""
        self.service_name = 'whatsapp_personal'
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize scraper
        self.scraper = WhatsAppScraper(
            session_data_path=self.config.get('session_data_path', 'auth/whatsapp_personal_session.json'),
            headless=self.config.get('headless', False),
            rate_limit_delay=self.config.get('rate_limit_delay', 1.0),
            max_retries=self.config.get('max_retries', 3)
        )
    
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
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get WhatsApp Personal service information."""
        return {
            "name": "WhatsApp Personal",
            "description": "WhatsApp Personal API with clean architecture",
            "icon": "📱",
            "color": "#25d366",
            "auth_url": "/whatsapp_personal/start_session",
            "callback_url": "/whatsapp_personal/start_session"
        }
    
    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Get WhatsApp Personal API endpoints."""
        return {
            # Session Management
            "start_session": {
                "method": "POST",
                "description": "Start WhatsApp Web session",
                "handler": self.start_session
            },
            "start_session_form": {
                "method": "GET",
                "description": "Show start session form",
                "handler": self.start_session_form
            },
            "close_session": {
                "method": "POST",
                "description": "Close WhatsApp Web session",
                "handler": self.close_session
            },
            "get_status": {
                "method": "GET",
                "description": "Get API status",
                "handler": self.get_status
            },
            "get_qr_code": {
                "method": "GET",
                "description": "Get QR code image",
                "handler": self.get_qr_code
            },
            
            # Message API - Multiple endpoints using same scraping function
            "get_messages": {
                "method": "GET",
                "description": "Get messages with configurable parameters",
                "handler": self.get_messages,
                "params": {
                    "limit": "Optional: Number of messages to retrieve (default: 10)",
                    "unread": "Optional: Filter for unread messages only (default: false)",
                    "chat": "Optional: Specific chat name to get messages from",
                    "contact": "Optional: Specific contact name (not implemented yet)"
                }
            },
            "get_latest_message": {
                "method": "GET",
                "description": "Get latest message from first unread chat",
                "handler": self.get_latest_message,
                "params": {}
            },
            "get_messages_from_chat": {
                "method": "GET",
                "description": "Get messages from specific chat",
                "handler": self.get_messages_from_chat,
                "params": {
                    "chat_name": "Required: Chat name to get messages from",
                    "limit": "Optional: Number of messages to retrieve (default: 10)"
                }
            },
            "get_unread_messages": {
                "method": "GET",
                "description": "Get unread messages from any chat",
                "handler": self.get_unread_messages,
                "params": {
                    "limit": "Optional: Number of messages to retrieve (default: 10)"
                }
            },
            "send_message": {
                "method": "POST",
                "description": "Send message to specific chat",
                "handler": self.send_message,
                "params": {
                    "chat_name": "Required: Chat name to send message to",
                    "message": "Required: Message text to send"
                }
            }
        }
    
    def is_authenticated(self) -> bool:
        """Check if WhatsApp session is authenticated."""
        try:
            status = self.scraper.get_status()
            return status.get('authenticated', False)
        except Exception as e:
            print(f"⚠️ Error checking authentication status: {e}")
            return False
    
    def _validate_limit_param(self, param_name: str, max_value: int) -> int:
        """Validate limit parameter."""
        try:
            value = request.args.get(param_name, max_value)
            limit = int(value) if value else max_value
            return min(limit, max_value)
        except (ValueError, TypeError):
            return max_value
    
    def _validate_required_param(self, param_name: str) -> str:
        """Validate required parameter."""
        try:
            import urllib.parse
            
            # Try to get from URL parameters first
            value = request.args.get(param_name)
            
            # If not found in URL params, try JSON body
            if not value and request.is_json:
                value = request.json.get(param_name)
            
            if not value:
                raise ValueError(f"Missing required parameter: {param_name}")
            
            # URL decode the value to handle Hebrew characters
            decoded_value = urllib.parse.unquote(str(value))
            return decoded_value
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid parameter {param_name}: {e}")
    
    # Session Management Endpoints
    def start_session(self) -> Dict[str, Any]:
        """Start WhatsApp Web session."""
        try:
            return self.scraper.start_session()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def start_session_form(self) -> str:
        """Show start session form with QR code popup."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WhatsApp Personal API - Start Session</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                .container { background: #f8f9fa; padding: 30px; border-radius: 10px; }
                .button { background: #25d366; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 8px 5px; cursor: pointer; border: none; }
                .button:hover { background: #1ea952; }
                .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
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
                        <li>A QR code will appear in a popup</li>
                        <li>Scan the QR code with your phone</li>
                        <li>The popup will close automatically when connected</li>
                    </ol>
                </div>
                
                <div style="text-align: center;">
                    <button onclick="startWhatsAppSession()" class="button" id="startButton">🔐 Start WhatsApp Personal Session</button>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <a href="/" class="button">← Back to Dashboard</a>
                    <a href="/whatsapp_personal/get_status" class="button">📊 Check Status</a>
                </div>
            </div>
            
            <script>
                function startWhatsAppSession() {
                    const startButton = document.getElementById('startButton');
                    startButton.disabled = true;
                    startButton.textContent = '🔄 Starting...';
                    
                    fetch('/whatsapp_personal/start_session', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            if (data.status === 'authenticated') {
                                alert('✅ Already authenticated! WhatsApp session is active.');
                                window.location.href = '/';
                            } else if (data.status === 'qr_ready') {
                                alert('📱 QR code ready! Please scan with your WhatsApp mobile app.');
                                window.location.href = '/';
                            }
                        } else {
                            alert('❌ Error: ' + (data.error || 'Failed to start session'));
                        }
                    })
                    .catch(error => {
                        alert('Network error: ' + error.message);
                    })
                    .finally(() => {
                        startButton.disabled = false;
                        startButton.textContent = '🔐 Start WhatsApp Personal Session';
                    });
                }
            </script>
        </body>
        </html>
        """
    
    def close_session(self) -> Dict[str, Any]:
        """Close WhatsApp Web session."""
        try:
            return self.scraper.close_session()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get API status."""
        try:
            return self.scraper.get_status()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Message Endpoints - All use the same scraping function with different parameters
    def get_messages(self) -> Dict[str, Any]:
        """Get messages with configurable parameters."""
        if not self.is_authenticated():
            return {"error": "Not authenticated. Please start session first."}
        
        try:
            # Parse parameters
            limit = self._validate_limit_param('limit', 10)
            unread = request.args.get('unread', 'false').lower() == 'true'
            chat = request.args.get('chat')
            contact = request.args.get('contact')  # Not implemented yet
            
            # Use unified scraping function
            return self.scraper.get_messages(limit=limit, unread=unread, chat=chat, contact=contact)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_latest_message(self) -> Dict[str, Any]:
        """Get latest message from first unread chat."""
        if not self.is_authenticated():
            return {"error": "Not authenticated. Please start session first."}
        
        try:
            # Use unified scraping function with specific parameters
            return self.scraper.get_messages(limit=1, unread=True)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_messages_from_chat(self) -> Dict[str, Any]:
        """Get messages from specific chat."""
        if not self.is_authenticated():
            return {"error": "Not authenticated. Please start session first."}
        
        try:
            chat_name = self._validate_required_param('chat_name')
            limit = self._validate_limit_param('limit', 10)
            
            # Use unified scraping function with specific parameters
            return self.scraper.get_messages(limit=limit, unread=False, chat=chat_name)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_unread_messages(self) -> Dict[str, Any]:
        """Get unread messages from any chat."""
        if not self.is_authenticated():
            return {"error": "Not authenticated. Please start session first."}
        
        try:
            limit = self._validate_limit_param('limit', 10)
            
            # Use unified scraping function with specific parameters
            return self.scraper.get_messages(limit=limit, unread=True)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_message(self) -> Dict[str, Any]:
        """Send message to specific chat."""
        if not self.is_authenticated():
            return {"error": "Not authenticated. Please start session first."}
        
        try:
            chat_name = self._validate_required_param('chat_name')
            message = self._validate_required_param('message')
            
            # Use scraping function
            return self.scraper.send_message(chat_name, message)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_qr_code(self) -> Dict[str, Any]:
        """Get QR code image."""
        try:
            if not self.scraper.auth_manager:
                return {"success": False, "error": "Authentication manager not initialized"}
            
            result = self.scraper.auth_manager.get_qr_code()
            return result
            
        except Exception as e:
            log_with_timestamp(f"Error in get_qr_code: {e}", "ERROR")
            return {"success": False, "error": str(e)}
    
    # Methods required by Flask app but not applicable to WhatsApp Personal API
    def get_auth_url(self) -> str:
        """Get auth URL - not applicable for WhatsApp Personal API."""
        return None
    
    def handle_callback(self, code: str) -> bool:
        """Handle callback - not applicable for WhatsApp Personal API."""
        return False
