"""Non-intrusive chat discovery for WhatsApp Personal API."""

import time
from typing import Dict, Any, List, Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from .utils import log_with_timestamp, extract_text_safely, is_element_displayed


class ChatDiscovery:
    """Discovers and tracks chats without reading messages."""
    
    def __init__(self, driver):
        """Initialize chat discovery."""
        self.driver = driver
        self.chat_states = {}
        self.last_scan_time = 0
        self.scan_interval = 30  # seconds
        
        # Chat selectors for sidebar - Only real chat elements
        self.chat_selectors = [
            # Primary modern WhatsApp selectors (most reliable)
            "div[data-testid='cell-frame-container']",
            "div[data-testid='chat-list'] div[data-testid='cell-frame-container']",
            
            # Fallback - only if primary doesn't work
            "div[data-testid='chat-list'] div[role='listitem']",
            "div[data-testid='chat-list'] > div"
        ]
    
    def scan_chat_list(self) -> Dict[str, Any]:
        """Scan chat list without reading messages."""
        current_time = time.time()
        
        # Skip if scanned recently
        if current_time - self.last_scan_time < self.scan_interval:
            return self.chat_states
        
        log_with_timestamp("Scanning chat list for discovery...")
        
        # Navigate to WhatsApp Web if not already there
        if "web.whatsapp.com" not in self.driver.current_url:
            self.driver.get("https://web.whatsapp.com")
            time.sleep(3)
        
        # Wait for chat list to load
        self._wait_for_chat_list_to_load()
        
        # Get current chat list from sidebar
        chat_elements = self._get_chat_elements()
        
        new_chat_states = {}
        valid_chat_count = 0
        
        for element in chat_elements:
            try:
                chat_info = self._extract_chat_info(element)
                
                # Skip if not a real chat (no name or ignored)
                if chat_info["name"] == "Unknown" or chat_info["name"] in ["רם שולח לעצמו דברים"]:
                    log_with_timestamp(f"Skipping non-chat element: {chat_info['name']}")
                    continue
                
                # This is a valid chat
                chat_id = self._get_chat_dom_id(element)
                new_chat_states[chat_id] = {
                    "name": chat_info["name"],
                    "unread_count": chat_info["unread_count"],
                    "last_activity": chat_info["last_activity"],
                    "dom_element": element,
                    "last_scan": current_time,
                    "has_new_messages": chat_info["unread_count"] > 0,
                    "chat_type": chat_info["chat_type"],
                    "order": valid_chat_count  # Correct order after filtering
                }
                
                log_with_timestamp(f"Chat {valid_chat_count + 1}: {chat_info['name']} (unread: {chat_info['unread_count']})")
                valid_chat_count += 1
                
            except Exception as e:
                log_with_timestamp(f"Error processing element: {e}", "WARNING")
                continue
        
        self.chat_states = new_chat_states
        self.last_scan_time = current_time
        
        log_with_timestamp(f"Discovered {len(self.chat_states)} chats")
        return self.chat_states
    
    def _wait_for_chat_list_to_load(self) -> None:
        """Wait for chat list to be visible and loaded."""
        log_with_timestamp("Waiting for chat list to load...")
        
        max_wait = 30  # seconds
        wait_interval = 2  # seconds
        attempts = 0
        
        while attempts < max_wait // wait_interval:
            try:
                # Check if any chat containers exist
                containers = [
                    "div[data-testid='chat-list']",
                    "div[data-testid='side']",
                    "div[role='application']"
                ]
                
                for container_selector in containers:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, container_selector)
                    if elements:
                        log_with_timestamp(f"Chat list loaded! Found container: {container_selector}")
                        return
                
                # Check if we can find any chat elements directly
                chat_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='cell-frame-container']")
                if chat_elements:
                    log_with_timestamp(f"Chat list loaded! Found {len(chat_elements)} chat elements")
                    return
                
                attempts += 1
                log_with_timestamp(f"Chat list not ready yet, waiting... (attempt {attempts})")
                time.sleep(wait_interval)
                
            except Exception as e:
                log_with_timestamp(f"Error waiting for chat list: {e}", "WARNING")
                time.sleep(wait_interval)
                attempts += 1
        
        log_with_timestamp("Chat list did not load within timeout period", "WARNING")
    
    def _get_chat_elements(self) -> List:
        """Get chat elements from sidebar in correct DOM order."""
        chat_elements = []
        
        # Debug: Check what containers exist
        log_with_timestamp("Debug: Checking for containers...")
        for container_selector in [
            "div[data-testid='chat-list']",
            "div[data-testid='side']", 
            "div[role='application']",
            "div[data-testid='app']",
            "div[data-testid='main']"
        ]:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, container_selector)
                log_with_timestamp(f"Found {len(elements)} elements for container: {container_selector}")
            except Exception as e:
                log_with_timestamp(f"Error checking container {container_selector}: {e}", "WARNING")
        
        # Try to find the main chat list container first
        chat_list_container = None
        for container_selector in [
            "div[data-testid='chat-list']",
            "div[data-testid='side']",
            "div[role='application']",
            "div[data-testid='app']"
        ]:
            try:
                container = self.driver.find_element(By.CSS_SELECTOR, container_selector)
                if container:
                    chat_list_container = container
                    log_with_timestamp(f"Found chat list container: {container_selector}")
                    break
            except:
                continue
        
        # Debug: Check what selectors work
        log_with_timestamp("Debug: Testing chat selectors...")
        for selector in self.chat_selectors:
            try:
                if chat_list_container:
                    elements = chat_list_container.find_elements(By.CSS_SELECTOR, selector)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                log_with_timestamp(f"Found {len(elements)} elements with selector: {selector}")
            except Exception as e:
                log_with_timestamp(f"Error with selector {selector}: {e}", "WARNING")
        
        if chat_list_container:
            # Get chat elements from the container in DOM order
            for selector in self.chat_selectors:
                try:
                    elements = chat_list_container.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        chat_elements.extend(elements)
                        log_with_timestamp(f"Found {len(elements)} chat elements with selector: {selector}")
                        break
                except Exception as e:
                    log_with_timestamp(f"Error with selector {selector}: {e}", "WARNING")
                    continue
        else:
            # Fallback to searching the entire page
            for selector in self.chat_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        chat_elements.extend(elements)
                        log_with_timestamp(f"Found {len(elements)} chat elements with selector: {selector}")
                        break
                except Exception as e:
                    log_with_timestamp(f"Error with selector {selector}: {e}", "WARNING")
                    continue
        
        log_with_timestamp(f"Total chat elements found: {len(chat_elements)}")
        return chat_elements
    
    def _get_chat_dom_id(self, element) -> str:
        """Get or generate unique DOM ID for chat element."""
        try:
            # Try to get existing DOM ID
            dom_id = element.get_attribute("id")
            if dom_id and dom_id.strip():
                return f"dom_{dom_id}"
            
            # Try to get data attributes
            for attr in ["data-id", "data-testid", "data-chat-id"]:
                try:
                    value = element.get_attribute(attr)
                    if value and value.strip():
                        return f"dom_{value}"
                except:
                    continue
            
            # Generate unique ID based on element properties
            element_hash = hash(str(element.location) + str(element.size))
            return f"dom_{abs(element_hash)}"
            
        except Exception as e:
            log_with_timestamp(f"Error getting DOM ID: {e}", "WARNING")
            return f"dom_{abs(hash(str(element)))}"
    
    def _extract_chat_info(self, element) -> Dict[str, Any]:
        """Extract chat information without reading messages."""
        try:
            # Extract chat name
            chat_name = self._extract_chat_name(element)
            
            # Extract unread count
            unread_count = self._extract_unread_count(element)
            
            # Extract last activity
            last_activity = self._extract_last_activity(element)
            
            # Determine chat type
            chat_type = self._determine_chat_type(element, chat_name)
            
            return {
                "name": chat_name,
                "unread_count": unread_count,
                "last_activity": last_activity,
                "chat_type": chat_type
            }
            
        except Exception as e:
            log_with_timestamp(f"Error extracting chat info: {e}", "WARNING")
            return {
                "name": "Unknown",
                "unread_count": 0,
                "last_activity": "",
                "chat_type": "unknown"
            }
    
    def _extract_chat_name(self, element) -> str:
        """Extract chat name from element - only return valid chat names."""
        try:
            # Check if this element has chat-like characteristics
            if not self._is_chat_element(element):
                return "Unknown"
            
            # Try title attributes first (most reliable)
            for attr in ["title", "aria-label"]:
                title = element.get_attribute(attr)
                if title and len(title.strip()) > 1:
                    return title.strip()
            
            # Try child elements with title
            for selector in ["span[title]", "div[title]"]:
                try:
                    child = element.find_element(By.CSS_SELECTOR, selector)
                    title = child.get_attribute("title")
                    if title and len(title.strip()) > 1:
                        return title.strip()
                except:
                    continue
            
            # Try text content
            text = extract_text_safely(element)
            if text:
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 1 and not line.isdigit():
                        return line
            
            return "Unknown"
            
        except Exception as e:
            return "Unknown"
    
    def _is_chat_element(self, element) -> bool:
        """Check if element looks like a chat item - be very strict."""
        try:
            # Must have chat-specific data-testid
            testid = element.get_attribute("data-testid")
            if testid not in ["cell-frame-container"]:
                return False
            
            # Must have clickable behavior
            if element.get_attribute("tabindex") != "0":
                return False
            
            # Must have a title attribute (chat names are in titles)
            if not element.get_attribute("title"):
                return False
            
            # Check child elements for chat title
            try:
                title_element = element.find_element(By.CSS_SELECTOR, "span[title], div[title]")
                title = title_element.get_attribute("title")
                if not title or len(title.strip()) < 2:
                    return False
            except:
                return False
                
            return True
        except:
            return False
    
    def _extract_unread_count(self, element) -> int:
        """Extract unread message count without reading messages."""
        try:
            # Look for unread badge
            unread_selectors = [
                "[data-testid='unread-count']",
                "span[data-testid='unread-count']",
                "div[data-testid='unread-count']",
                ".unread-count",
                "[aria-label*='unread']"
            ]
            
            for selector in unread_selectors:
                try:
                    unread_element = element.find_element(By.CSS_SELECTOR, selector)
                    if unread_element and is_element_displayed(unread_element):
                        unread_text = extract_text_safely(unread_element)
                        if unread_text and unread_text.isdigit():
                            return int(unread_text)
                except:
                    continue
            
            return 0
            
        except Exception as e:
            log_with_timestamp(f"Error extracting unread count: {e}", "WARNING")
            return 0
    
    def _extract_last_activity(self, element) -> str:
        """Extract last activity timestamp."""
        try:
            # Look for timestamp elements
            time_selectors = [
                "span[data-testid='msg-time']",
                "span[data-testid='time']",
                "div[data-testid='time']",
                "span[title*=':']"
            ]
            
            for selector in time_selectors:
                try:
                    time_element = element.find_element(By.CSS_SELECTOR, selector)
                    time_text = extract_text_safely(time_element)
                    if time_text and (":" in time_text or "AM" in time_text or "PM" in time_text):
                        return time_text
                except:
                    continue
            
            return ""
            
        except Exception as e:
            log_with_timestamp(f"Error extracting last activity: {e}", "WARNING")
            return ""
    
    def _determine_chat_type(self, element, chat_name: str) -> str:
        """Determine if chat is individual or group."""
        try:
            # Check for group indicators
            full_text = extract_text_safely(element)
            
            # Group chat indicators
            group_indicators = [
                "," in chat_name,  # Multiple names
                "You" in full_text,  # Group chat indicator
                len(full_text.split('\n')) > 2,  # Multiple lines
                chat_name.count(' ') > 3  # Multiple words
            ]
            
            if any(group_indicators):
                return "group"
            else:
                return "individual"
                
        except Exception as e:
            log_with_timestamp(f"Error determining chat type: {e}", "WARNING")
            return "unknown"
    
    def get_unread_summary(self) -> Dict[str, Any]:
        """Get summary of unread messages across all chats."""
        chat_states = self.scan_chat_list()
        
        total_unread = 0
        chats_with_unread = 0
        unread_by_chat = {}
        
        for chat_id, state in chat_states.items():
            unread_count = state["unread_count"]
            if unread_count > 0:
                total_unread += unread_count
                chats_with_unread += 1
                unread_by_chat[state["name"]] = unread_count
        
        return {
            "total_unread": total_unread,
            "chats_with_unread": chats_with_unread,
            "unread_by_chat": unread_by_chat,
            "scan_time": self.last_scan_time
        }
    
    def get_chat_discovery(self) -> Dict[str, Any]:
        """Get chat discovery data."""
        chat_states = self.scan_chat_list()
        
        chats = []
        for chat_id, state in chat_states.items():
            chats.append({
                "chat_id": chat_id,
                "name": state["name"],
                "unread_count": state["unread_count"],
                "last_activity": state["last_activity"],
                "has_new_messages": state["has_new_messages"],
                "chat_type": state["chat_type"]
            })
        
        return {
            "chats": chats,
            "total_chats": len(chats),
            "scan_time": self.last_scan_time
        }
    
    def find_chat_by_name(self, chat_name: str) -> Optional[Dict[str, Any]]:
        """Find chat by name without reading messages."""
        chat_states = self.scan_chat_list()
        
        for chat_id, state in chat_states.items():
            if state["name"].lower() == chat_name.lower():
                return {
                    "chat_id": chat_id,
                    "name": state["name"],
                    "unread_count": state["unread_count"],
                    "last_activity": state["last_activity"],
                    "has_new_messages": state["has_new_messages"],
                    "chat_type": state["chat_type"],
                    "dom_element": state["dom_element"]
                }
        
        return None
