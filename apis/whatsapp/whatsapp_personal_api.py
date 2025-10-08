"""WhatsApp Personal API implementation using web scraping."""
from typing import Dict, Any, List, Optional
import sys
import os
import time
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import threading
import queue

class WhatsAppPersonalAPI:
    """WhatsApp Personal API using web scraping."""
    
    def __init__(self, session_data_path: str = None, headless: bool = False, 
                 rate_limit_delay: float = 1.0, max_retries: int = 3):
        """Initialize WhatsApp Personal API with web scraping."""
        self.session_data_path = session_data_path or 'auth/whatsapp_personal_session.json'
        self.headless = headless
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.driver = None
        self.wait = None
        self.is_authenticated = False
        self.session_data = self._load_session_data()
        self._message_queue = queue.Queue()
        self._is_processing_messages = False
        
    def _load_session_data(self) -> Dict[str, Any]:
        """Load session data from file."""
        try:
            if Path(self.session_data_path).exists():
                with open(self.session_data_path, 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load session data: {e}")
        return {}
    
    def _save_session_data(self) -> None:
        """Save session data to file."""
        try:
            Path(self.session_data_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_data_path, 'w') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save session data: {e}")
    
    def _setup_driver(self) -> None:
        """Setup Chrome WebDriver with WhatsApp Web optimized settings."""
        if self.driver:
            return
            
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # WhatsApp Web specific optimizations
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Disable images and CSS for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            # Try to get ChromeDriver path
            driver_path = ChromeDriverManager().install()
            if not driver_path:
                raise Exception("ChromeDriverManager returned None - likely Docker environment issue")
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            print("✅ Chrome WebDriver initialized successfully")
        except Exception as e:
            # Provide helpful error message for Docker users
            error_msg = f"Failed to initialize Chrome WebDriver: {e}"
            if "Docker" in str(e) or "None" in str(e):
                error_msg += "\n\n💡 This is expected in Docker without display. Try running locally:"
                error_msg += "\n   1. Stop Docker: docker compose down"
                error_msg += "\n   2. Run locally: python api_server.py"
                error_msg += "\n   3. Access: http://localhost:8081/whatsapp/auth"
            raise Exception(error_msg)
    
    def _wait_for_element(self, by: By, value: str, timeout: int = 20) -> Any:
        """Wait for element with timeout."""
        try:
            return self.wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            raise Exception(f"Element not found: {value}")
    
    def _wait_for_clickable(self, by: By, value: str, timeout: int = 20) -> Any:
        """Wait for clickable element with timeout."""
        try:
            return self.wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            raise Exception(f"Element not clickable: {value}")
    
    def _safe_click(self, element) -> bool:
        """Safely click element with retry logic."""
        for attempt in range(self.max_retries):
            try:
                self.driver.execute_script("arguments[0].click();", element)
                time.sleep(0.5)
                return True
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                print(f"Failed to click element after {self.max_retries} attempts: {e}")
                return False
        return False
    
    def _safe_send_keys(self, element, text: str) -> bool:
        """Safely send keys to element with retry logic."""
        for attempt in range(self.max_retries):
            try:
                element.clear()
                element.send_keys(text)
                time.sleep(0.5)
                return True
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                print(f"Failed to send keys after {self.max_retries} attempts: {e}")
                return False
        return False
    
    def start_session(self) -> Dict[str, Any]:
        """Start WhatsApp Web session."""
        try:
            self._setup_driver()
            self.driver.get("https://web.whatsapp.com")
            
            # Wait for QR code or main interface
            try:
                # Check if already logged in
                self.wait_for_main_interface()
                self.is_authenticated = True
                return {"success": True, "message": "Already authenticated"}
            except TimeoutException:
                # Need to scan QR code
                return self._handle_qr_scan()
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_qr_scan(self) -> Dict[str, Any]:
        """Handle QR code scanning process."""
        try:
            # Wait for QR code to appear
            qr_code = self._wait_for_element(By.CSS_SELECTOR, "canvas[aria-label='Scan me!']", timeout=30)
            
            # Wait for user to scan QR code
            print("📱 Please scan the QR code with your WhatsApp mobile app")
            print("⏳ Waiting for authentication...")
            
            # Wait for main interface to load (indicating successful login)
            self.wait_for_main_interface()
            self.is_authenticated = True
            
            # Save session data
            self.session_data['authenticated'] = True
            self.session_data['last_login'] = datetime.now().isoformat()
            self._save_session_data()
            
            return {"success": True, "message": "Successfully authenticated"}
            
        except TimeoutException:
            return {"success": False, "error": "QR code scan timeout - please try again"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def wait_for_main_interface(self) -> None:
        """Wait for WhatsApp main interface to load."""
        # Wait for the main chat list to appear
        self._wait_for_element(By.CSS_SELECTOR, "[data-testid='chat-list']", timeout=30)
        time.sleep(2)  # Additional wait for full load
    
    def get_contacts(self, limit: int = 50) -> Dict[str, Any]:
        """Get list of contacts from WhatsApp."""
        if not self.is_authenticated:
            return {"error": "Not authenticated. Please start session first."}
        
        try:
            contacts = []
            
            # Scroll to load more contacts
            chat_list = self._wait_for_element(By.CSS_SELECTOR, "[data-testid='chat-list']")
            
            # Get initial contacts
            contact_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='cell-frame-container']")
            
            for i, element in enumerate(contact_elements[:limit]):
                try:
                    # Get contact name
                    name_element = element.find_element(By.CSS_SELECTOR, "[data-testid='cell-frame-title']")
                    name = name_element.text.strip()
                    
                    # Get last message preview
                    try:
                        message_element = element.find_element(By.CSS_SELECTOR, "[data-testid='last-msg-lbl']")
                        last_message = message_element.text.strip()
                    except NoSuchElementException:
                        last_message = ""
                    
                    # Get timestamp
                    try:
                        time_element = element.find_element(By.CSS_SELECTOR, "[data-testid='msg-meta-time']")
                        timestamp = time_element.text.strip()
                    except NoSuchElementException:
                        timestamp = ""
                    
                    # Get unread count
                    try:
                        unread_element = element.find_element(By.CSS_SELECTOR, "[data-testid='unread-count']")
                        unread_count = int(unread_element.text.strip())
                    except NoSuchElementException:
                        unread_count = 0
                    
                    contacts.append({
                        "name": name,
                        "last_message": last_message,
                        "timestamp": timestamp,
                        "unread_count": unread_count,
                        "index": i
                    })
                    
                except Exception as e:
                    print(f"Error processing contact {i}: {e}")
                    continue
            
            return {
                "success": True,
                "contacts": contacts,
                "total_found": len(contacts)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_conversations(self, limit: int = 20) -> Dict[str, Any]:
        """Get list of conversations."""
        if not self.is_authenticated:
            return {"error": "Not authenticated. Please start session first."}
        
        try:
            conversations = []
            
            # Get conversation elements
            chat_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='cell-frame-container']")
            
            for i, element in enumerate(chat_elements[:limit]):
                try:
                    # Click on conversation to get details
                    self._safe_click(element)
                    time.sleep(1)
                    
                    # Get conversation name
                    try:
                        name_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='conversation-header']")
                        name = name_element.text.strip()
                    except NoSuchElementException:
                        name = f"Conversation {i+1}"
                    
                    # Get message count in current conversation
                    messages = self.get_messages_from_current_chat(limit=10)
                    
                    conversations.append({
                        "name": name,
                        "message_count": len(messages.get("messages", [])),
                        "last_activity": messages.get("last_activity", ""),
                        "index": i
                    })
                    
                except Exception as e:
                    print(f"Error processing conversation {i}: {e}")
                    continue
            
            return {
                "success": True,
                "conversations": conversations,
                "total_found": len(conversations)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_conversation(self, search_term: str) -> Dict[str, Any]:
        """Search for conversations by name."""
        if not self.is_authenticated:
            return {"error": "Not authenticated. Please start session first."}
        
        try:
            # Click on search
            search_button = self._wait_for_clickable(By.CSS_SELECTOR, "[data-testid='search']")
            self._safe_click(search_button)
            time.sleep(1)
            
            # Enter search term
            search_input = self._wait_for_element(By.CSS_SELECTOR, "[data-testid='search-input']")
            self._safe_send_keys(search_input, search_term)
            time.sleep(2)
            
            # Get search results
            results = []
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='cell-frame-container']")
            
            for element in result_elements:
                try:
                    name_element = element.find_element(By.CSS_SELECTOR, "[data-testid='cell-frame-title']")
                    name = name_element.text.strip()
                    
                    if search_term.lower() in name.lower():
                        results.append({
                            "name": name,
                            "element": element
                        })
                except NoSuchElementException:
                    continue
            
            # Clear search
            search_input.clear()
            search_input.send_keys(Keys.ESCAPE)
            
            return {
                "success": True,
                "results": results,
                "search_term": search_term,
                "total_found": len(results)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_messages_from_current_chat(self, limit: int = 50) -> Dict[str, Any]:
        """Get messages from currently open chat."""
        if not self.is_authenticated:
            return {"error": "Not authenticated. Please start session first."}
        
        try:
            messages = []
            
            # Scroll up to load more messages
            message_container = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='conversation-panel-messages']")
            
            # Scroll up to load more messages
            for _ in range(3):
                self.driver.execute_script("arguments[0].scrollTop = 0;", message_container)
                time.sleep(1)
            
            # Get message elements
            message_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='msg-container']")
            
            for element in message_elements[-limit:]:  # Get last N messages
                try:
                    # Get message text
                    try:
                        text_element = element.find_element(By.CSS_SELECTOR, "[data-testid='msg-text']")
                        text = text_element.text.strip()
                    except NoSuchElementException:
                        text = ""
                    
                    # Get timestamp
                    try:
                        time_element = element.find_element(By.CSS_SELECTOR, "[data-testid='msg-meta-time']")
                        timestamp = time_element.text.strip()
                    except NoSuchElementException:
                        timestamp = ""
                    
                    # Determine if message is from me or other
                    is_from_me = "message-out" in element.get_attribute("class")
                    
                    messages.append({
                        "text": text,
                        "timestamp": timestamp,
                        "is_from_me": is_from_me,
                        "message_id": element.get_attribute("data-id") or f"msg_{len(messages)}"
                    })
                    
                except Exception as e:
                    print(f"Error processing message: {e}")
                    continue
            
            return {
                "success": True,
                "messages": messages,
                "total_found": len(messages),
                "last_activity": messages[0]["timestamp"] if messages else ""
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_message(self, contact_name: str, message: str) -> Dict[str, Any]:
        """Send message to a contact."""
        if not self.is_authenticated:
            return {"error": "Not authenticated. Please start session first."}
        
        try:
            # Search for contact
            search_result = self.search_conversation(contact_name)
            if not search_result["success"] or not search_result["results"]:
                return {"success": False, "error": f"Contact '{contact_name}' not found"}
            
            # Click on first result
            first_result = search_result["results"][0]
            self._safe_click(first_result["element"])
            time.sleep(2)
            
            # Find message input
            message_input = self._wait_for_element(By.CSS_SELECTOR, "[data-testid='conversation-compose-box-input']")
            
            # Type message
            self._safe_send_keys(message_input, message)
            time.sleep(1)
            
            # Send message
            message_input.send_keys(Keys.ENTER)
            time.sleep(1)
            
            return {
                "success": True,
                "message": f"Message sent to {contact_name}",
                "contact": contact_name,
                "text": message
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get API status."""
        return {
            "service": "whatsapp_personal",
            "authenticated": self.is_authenticated,
            "status": "ready" if self.is_authenticated else "not_authenticated",
            "session_data_path": self.session_data_path,
            "headless": self.headless
        }
    
    def close_session(self) -> Dict[str, Any]:
        """Close WhatsApp session."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self.is_authenticated = False
            
            return {"success": True, "message": "Session closed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def __del__(self):
        """Cleanup on destruction."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

