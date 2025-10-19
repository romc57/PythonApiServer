"""WhatsApp Scraper - All scraping logic with unified functions."""

import time
import threading
import json
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

from .webdriver_manager import WebDriverManager
from .authentication import AuthenticationManager
from .chat_discovery import ChatDiscovery
from .message_reader import MessageReader 
from .utils import log_with_timestamp


class WhatsAppScraper:
    """WhatsApp Scraper - Unified scraping functions with proper error handling."""
    
    def __init__(self, session_data_path: str = None, headless: bool = False, 
                 rate_limit_delay: float = 1.0, max_retries: int = 3):
        """Initialize WhatsApp Scraper."""
        self.session_data_path = session_data_path or 'auth/whatsapp_personal_session.json'
        self.headless = headless
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        
        # Initialize components
        self.webdriver_manager = WebDriverManager(self.session_data_path, headless)
        self.auth_manager = None
        self.chat_discovery = None
        self.message_reader = None
        
        # Performance optimization: Chat ID caching
        self.chat_id_cache = {}  # Maps chat_name -> {"dom_element": element, "last_updated": timestamp}
        self.cache_update_interval = 5  # seconds
        self.last_cache_update = 0
        
        # Background monitoring
        self._monitoring_thread = None
        self._monitoring_running = False
        
        # Try to restore session if it was previously authenticated
        self._try_restore_session()
    
    @property
    def driver(self):
        """Get WebDriver instance."""
        return self.webdriver_manager.get_driver()
    
    @property
    def wait(self):
        """Get WebDriverWait instance."""
        return self.webdriver_manager.get_wait()
    
    @property
    def is_authenticated(self):
        """Get authentication status."""
        return self.auth_manager.is_authenticated if self.auth_manager else False
    
    def _try_restore_session(self) -> None:
        """Try to restore a previously authenticated session."""
        try:
            log_with_timestamp("=== STARTING WHATSAPP SESSION RESTORATION ===")
            # Check if we have any Chrome profile directories
            from pathlib import Path
            auth_dir = Path(self.session_data_path).parent
            
            # Look for any existing WhatsApp Chrome profiles
            simple_profile = auth_dir / "whatsapp_chrome_profile"
            existing_profiles = list(auth_dir.glob("whatsapp_chrome_profile_*"))
            
            log_with_timestamp(f"WhatsApp Session Restoration: Found simple profile: {simple_profile.exists()}, Found {len(existing_profiles)} timestamped profiles")
            log_with_timestamp(f"Profile path: {simple_profile}")
            log_with_timestamp(f"Auth dir: {auth_dir}")
            
            if simple_profile.exists() or existing_profiles:
                # Prioritize the simple profile if it exists
                if simple_profile.exists():
                    log_with_timestamp(f"Using simple profile: {simple_profile.name}")
                else:
                    # Use the most recent timestamped profile
                    latest_profile = max(existing_profiles, key=lambda p: p.stat().st_mtime)
                    log_with_timestamp(f"Using latest profile: {latest_profile.name}")
                
                # Initialize WebDriver with existing profile
                self.webdriver_manager.setup_driver()
                
                # Initialize managers
                self._initialize_managers()
                
                # Navigate to WhatsApp Web
                self.driver.get("https://web.whatsapp.com")
                log_with_timestamp("Waiting for WhatsApp Web to load (Chrome restoring session)...")
                time.sleep(45)  # Give more time for page to fully load and restore
                
                # Check current URL and page state
                current_url = self.driver.current_url
                log_with_timestamp(f"Current URL after loading: {current_url}")
                
                # Wait for session restoration with multiple attempts (like reopening Chrome browser)
                max_attempts = 12
                for attempt in range(max_attempts):
                    log_with_timestamp(f"Session restoration attempt {attempt + 1}/{max_attempts}")
                    
                    # Check if session was restored successfully
                    if self.auth_manager.check_authentication_status():
                        self.auth_manager.is_authenticated = True
                        log_with_timestamp("WhatsApp session restored automatically!")
                        self.auth_manager._update_session_data_on_auth()
                        self._start_background_monitoring()
                        return
                    
                    # If not connected, wait and try again
                    log_with_timestamp(f"Session not restored yet, waiting... (attempt {attempt + 1})")
                    time.sleep(20)
                
                # If all attempts failed, try refreshing the page
                log_with_timestamp("All restoration attempts failed, trying page refresh...")
                self.driver.refresh()
                time.sleep(30)
                
                # Final check after refresh
                if self.auth_manager.check_authentication_status():
                    self.auth_manager.is_authenticated = True
                    log_with_timestamp("WhatsApp session restored after refresh!")
                    self.auth_manager._update_session_data_on_auth()
                    self._start_background_monitoring()
                else:
                    log_with_timestamp("WhatsApp session expired - QR code scan needed")
                    self.auth_manager.is_authenticated = False
            else:
                log_with_timestamp("No Chrome profile found - first time setup required")
                        
        except Exception as e:
            log_with_timestamp(f"Error during session restoration: {e}", "ERROR")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.webdriver_manager.quit()
    
    def _initialize_managers(self) -> None:
        """Initialize all manager components."""
        self.auth_manager = AuthenticationManager(self.driver, self.session_data_path)
        self.chat_discovery = ChatDiscovery(self.driver)
        self.message_reader = MessageReader(self.driver)
    
    # Session Management Functions
    def start_session(self) -> Dict[str, Any]:
        """Start WhatsApp Web session."""
        try:
            # Setup WebDriver if not already done
            self.webdriver_manager.setup_driver()
            
            # Initialize managers if not already done
            if not self.auth_manager:
                self._initialize_managers()
            
            # Use authentication manager to start session
            result = self.auth_manager.start_session()
            
            if result.get("success") and result.get("status") == "authenticated":
                # Start background monitoring
                self._start_background_monitoring()
            
            return result
            
        except Exception as e:
            log_with_timestamp(f"Error starting WhatsApp session: {e}", "ERROR")
            return {
                "success": False, 
                "error": str(e),
                "status": "error"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get API status with real-time authentication check."""
        if not self.auth_manager:
            return {
                "service": "whatsapp_personal",
                "authenticated": False,
                "status": "not_initialized",
                "error": "Managers not initialized"
            }
        
        return self.auth_manager.get_status()
    
    def close_session(self) -> Dict[str, Any]:
        """Close WhatsApp session."""
        try:
            self._stop_background_monitoring()
            self.webdriver_manager.quit()
            
            return {"success": True, "message": "Session closed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Unified Message Function - DRY Principle (Modular)
    def get_messages(self, limit: int = 10, unread: bool = False, chat: str = None, contact: str = None) -> Dict[str, Any]:
        """Unified function to get messages with configurable parameters.
        
        Args:
            limit: Number of messages to retrieve
            unread: If True, only get unread messages; if False, get all messages; if None, get latest regardless of read status
            chat: Specific chat name to get messages from
            contact: Specific contact name (maps to personal chat)
        
        Returns:
            Dict with success status, messages, and metadata
        """
        if not self.auth_manager.check_authentication_status():
            return {"error": "Not authenticated. Please scan QR code first."}
        
        try:
            # Update chat cache if needed
            self._update_chat_cache_if_needed()
            
            # Determine target chat
            target_chat = self._determine_target_chat(chat, contact)
            
            if target_chat:
                # Get messages from specific chat
                return self._get_messages_from_cached_chat(target_chat, limit, unread)
            else:
                # Get messages from any chat based on criteria
                if unread is True:
                    return self._get_unread_messages_from_any_chat(limit)
                else:
                    return self._get_latest_messages_from_any_chat(limit)
                
        except Exception as e:
            log_with_timestamp(f"Error getting messages: {e}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def _update_chat_cache_if_needed(self) -> None:
        """Update chat cache if it's time to refresh."""
        current_time = time.time()
        if current_time - self.last_cache_update > self.cache_update_interval:
            self._update_chat_cache()
            self.last_cache_update = current_time
    
    def _force_update_chat_cache(self) -> None:
        """Force update chat cache immediately."""
        log_with_timestamp("Force updating chat cache...")
        self._update_chat_cache()
        self.last_cache_update = time.time()
    
    def _update_chat_cache(self) -> None:
        """Update the chat ID cache with current DOM state."""
        try:
            log_with_timestamp("Updating chat ID cache...")
            chat_states = self.chat_discovery.scan_chat_list()
            
            # Clear existing cache
            self.chat_id_cache.clear()
            
            # Sort chats by order and update cache
            sorted_chats = sorted(chat_states.items(), 
                                key=lambda x: x[1].get("order", 999))
            
            for chat_id, state in sorted_chats:
                chat_name = state.get("name", f"Chat_{chat_id}")
                if chat_name != "Unknown":  # Skip unknown chats
                    self.chat_id_cache[chat_name] = {
                        "dom_element": state["dom_element"],
                        "last_updated": time.time(),
                        "unread_count": state.get("unread_count", 0),
                        "last_message": state.get("last_message", ""),
                        "order": state.get("order", 999)
                    }
                    log_with_timestamp(f"Cached chat: {chat_name} (order: {state.get('order', 999)})")
            
            log_with_timestamp(f"Updated chat cache with {len(self.chat_id_cache)} chats")
            
        except Exception as e:
            log_with_timestamp(f"Error updating chat cache: {e}", "ERROR")
    
    def _determine_target_chat(self, chat: str = None, contact: str = None) -> str:
        """Determine which chat to target based on parameters."""
        if chat:
            return chat
        elif contact:
            # For contacts, look for personal chat (not group chat)
            for cached_chat_name, cached_data in self.chat_id_cache.items():
                if contact.lower() in cached_chat_name.lower() and "group" not in cached_chat_name.lower():
                    return cached_chat_name
            return None
        else:
            return None
    
    def _get_messages_from_cached_chat(self, chat_name: str, limit: int, unread: bool = None) -> Dict[str, Any]:
        """Get messages from a cached chat using DOM element."""
        try:
            if chat_name not in self.chat_id_cache:
                return {"success": False, "error": f"Chat '{chat_name}' not found in cache"}
            
            cached_data = self.chat_id_cache[chat_name]
            dom_element = cached_data["dom_element"]
            
            # Read messages from the cached DOM element
            result = self.message_reader.read_messages_from_chat(dom_element, limit)
            
            if result["success"] and result["messages"]:
                # Filter messages based on unread parameter
                messages = self._filter_messages_by_read_status(result["messages"], unread)
                limited_messages = messages[-limit:] if limit else messages
                
                # Mark messages as read if explicitly requested
                if unread is False:  # Only mark as read when explicitly getting read messages
                    self._mark_messages_as_read(limited_messages)
                
                return self._format_message_response(limited_messages, chat_name, f"Retrieved {len(limited_messages)} messages from {chat_name}")
            else:
                return self._format_message_response([], chat_name, "No messages found")
                
        except Exception as e:
            log_with_timestamp(f"Error getting messages from cached chat {chat_name}: {e}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def _filter_messages_by_read_status(self, messages: List[Dict], unread: bool = None) -> List[Dict]:
        """Filter messages based on read status."""
        if unread is None:
            return messages  # Return all messages
        elif unread is True:
            return [msg for msg in messages if not msg.get("is_read", True)]
        else:  # unread is False
            return [msg for msg in messages if msg.get("is_read", True)]
    
    def _mark_messages_as_read(self, messages: List[Dict]) -> None:
        """Mark messages as read (placeholder for future implementation)."""
        # This would interact with WhatsApp's read status system
        # For now, we'll just update our internal tracking
        for message in messages:
            message["is_read"] = True
    
    def _get_messages_from_specific_chat(self, chat: str, limit: int, unread: bool) -> Dict[str, Any]:
        """Get messages from a specific chat."""
        chat_info = self.chat_discovery.find_chat_by_name(chat)
        if not chat_info:
            return {"success": False, "error": f"Chat '{chat}' not found"}
        
        result = self.message_reader.read_messages_from_chat(chat_info["dom_element"], limit)
        
        if result["success"] and result["messages"]:
            messages = self._filter_and_limit_messages(result["messages"], limit, unread)
            return self._format_message_response(messages, result["chat_name"], f"Retrieved {len(messages)} messages from {chat}")
        else:
            return self._format_message_response([], chat, "No messages found")
    
    def _get_unread_messages_from_any_chat(self, limit: int) -> Dict[str, Any]:
        """Get unread messages from any chat using cached data."""
        try:
            # Find chats with unread messages from cache
            unread_chats = []
            for chat_name, cached_data in self.chat_id_cache.items():
                if cached_data.get("unread_count", 0) > 0:
                    unread_chats.append((chat_name, cached_data))
            
            if not unread_chats:
                return self._format_message_response([], None, "No unread messages")
            
            # Get messages from the first chat with unread messages
            chat_name, cached_data = unread_chats[0]
            dom_element = cached_data["dom_element"]
            
            result = self.message_reader.read_messages_from_chat(dom_element, limit)
            
            if result["success"] and result["messages"]:
                # Filter for unread messages (not from me)
                unread_messages = [msg for msg in result["messages"] if not msg.get("is_from_me", True)]
                limited_messages = unread_messages[-limit:] if limit else unread_messages
                
                # Mark as read after retrieval
                self._mark_messages_as_read(limited_messages)
                
                return self._format_message_response(limited_messages, chat_name, f"Retrieved {len(limited_messages)} unread messages from {chat_name}")
            
            return self._format_message_response([], chat_name, "No unread messages found")
            
        except Exception as e:
            log_with_timestamp(f"Error getting unread messages: {e}", "ERROR")
            return self._format_message_response([], None, f"Error: {str(e)}")
    
    def _get_latest_messages_from_any_chat(self, limit: int) -> Dict[str, Any]:
        """Get latest messages from any chat using cached data - use first chat in DOM order."""
        try:
            # Force cache update to get latest chat order
            self._force_update_chat_cache()
            
            # Get chats sorted by their DOM order (first chat should be first)
            sorted_chats = sorted(self.chat_id_cache.items(), 
                                key=lambda x: x[1].get("order", 999))
            
            if not sorted_chats:
                return self._format_message_response([], None, "No chats found")
            
            # Try first chat (should be the first one in DOM)
            chat_name, cached_data = sorted_chats[0]
            dom_element = cached_data["dom_element"]
            
            log_with_timestamp(f"Trying first chat in DOM order: {chat_name}")
            
            result = self.message_reader.read_messages_from_chat(dom_element, limit)
            
            if result["success"] and result["messages"]:
                return self._format_message_response(result["messages"], chat_name, f"Retrieved {len(result['messages'])} latest messages from {chat_name}")
            
            # If first chat has no messages, try other chats
            for chat_name, cached_data in sorted_chats[1:]:
                log_with_timestamp(f"Trying other chat: {chat_name}")
                dom_element = cached_data["dom_element"]
                result = self.message_reader.read_messages_from_chat(dom_element, limit)
                
                if result["success"] and result["messages"]:
                    return self._format_message_response(result["messages"], chat_name, f"Retrieved {len(result['messages'])} latest messages from {chat_name}")
            
            return self._format_message_response([], chat_name, "No messages found in any chat")
            
        except Exception as e:
            log_with_timestamp(f"Error getting latest messages: {e}", "ERROR")
            return self._format_message_response([], None, f"Error: {str(e)}")
    
    def _filter_and_limit_messages(self, messages: List[Dict], limit: int, unread: bool) -> List[Dict]:
        """Filter messages by unread status and apply limit."""
        if unread:
            messages = [msg for msg in messages if not msg.get("is_from_me", True)]
        
        return messages[-limit:] if limit else messages
    
    def _format_message_response(self, messages: List[Dict], chat_name: str, status: str) -> Dict[str, Any]:
        """Format message response consistently."""
        return {
            "success": True,
            "messages": messages,
            "chat_name": chat_name,
            "count": len(messages),
            "status": status
        }
    
    def send_message(self, chat_name: str, message: str) -> Dict[str, Any]:
        """Send message to specific chat using cached data."""
        if not self.auth_manager.check_authentication_status():
            return {"error": "Not authenticated. Please scan QR code first."}
        
        try:
            # Force cache update to get latest chat order
            self._force_update_chat_cache()
            
            # Find chat in cache
            if chat_name not in self.chat_id_cache:
                return {"success": False, "error": f"Chat '{chat_name}' not found in cache. Available chats: {list(self.chat_id_cache.keys())}"}
            
            cached_data = self.chat_id_cache[chat_name]
            dom_element = cached_data["dom_element"]
            
            log_with_timestamp(f"Sending message to {chat_name}")
            
            # Open chat
            dom_element.click()
            time.sleep(3)  # Wait longer for chat to open
            
            # Send message
            result = self.message_reader.send_message_to_chat(message)
            
            # Force update cache after sending message
            if result.get("success"):
                self._force_update_chat_cache()
            
            return result
            
        except Exception as e:
            log_with_timestamp(f"Error sending message: {e}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def check_authentication_status(self) -> bool:
        """Check if WhatsApp Web is currently authenticated."""
        if not self.auth_manager:
            return False
        
        return self.auth_manager.check_authentication_status()
    
    # Background Monitoring
    def _start_background_monitoring(self) -> None:
        """Start background monitoring thread."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return
        
        self._monitoring_running = True
        self._monitoring_thread = threading.Thread(target=self._background_monitor, daemon=True)
        self._monitoring_thread.start()
        log_with_timestamp("WhatsApp background monitoring started")
    
    def _stop_background_monitoring(self) -> None:
        """Stop background monitoring thread."""
        self._monitoring_running = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        log_with_timestamp("WhatsApp background monitoring stopped")
    
    def _background_monitor(self) -> None:
        """Background monitoring worker thread."""
        while self._monitoring_running and self.is_authenticated:
            try:
                if self.driver and self.is_authenticated:
                    # Check if we're still on WhatsApp Web
                    if "web.whatsapp.com" not in self.driver.current_url:
                        self.driver.get("https://web.whatsapp.com")
                        time.sleep(2)
                    
                    # Perform non-intrusive chat discovery
                    self.chat_discovery.scan_chat_list()
                
                # Wait 30 seconds before next check
                time.sleep(30)
                
            except Exception as e:
                log_with_timestamp(f"Background monitoring error: {e}", "ERROR")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def __del__(self):
        """Cleanup on destruction."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
