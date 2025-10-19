"""Message reading for WhatsApp Personal API."""

import time
from typing import Dict, Any, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from .utils import log_with_timestamp, extract_text_safely, is_element_displayed


class MessageReader:
    """Reads messages from specific chats when explicitly requested."""
    
    def __init__(self, driver):
        """Initialize message reader."""
        self.driver = driver
        
        # Message selectors - Comprehensive and modern WhatsApp Web selectors
        self.message_selectors = [
            # Primary modern WhatsApp selectors (most reliable)
            "div[data-testid='msg-container']",
            "div[data-testid='conversation-panel-messages'] div[data-testid='msg-container']",
            "div[role='application'] div[data-testid='msg-container']",
            
            # Alternative modern selectors
            "div[data-testid='msg-container'] > div",
            "div[data-testid='conversation-panel-messages'] > div",
            "div[role='application'] > div",
            
            # Message bubble selectors
            "div[data-testid='msg-container'] div[data-testid='msg']",
            "div[data-testid='conversation-panel-messages'] div[data-testid='msg']",
            "div[role='application'] div[data-testid='msg']",
            
            # Fallback selectors for different WhatsApp versions
            "div[data-id*='msg']",
            "div[aria-label*='message']",
            "div[class*='message']",
            "div[class*='msg']",
            "div[class*='Message']",
            "div[class*='Msg']",
            
            # Generic message containers
            "div[role='listitem']",
            "div[class*='conversation'] div[class*='message']",
            "div[class*='chat'] div[class*='message']",
            "div[class*='conversation'] div[class*='msg']",
            "div[class*='chat'] div[class*='msg']",
            
            # Additional fallback selectors
            "div[class*='message-in']",
            "div[class*='message-out']",
            "div[class*='msg-in']",
            "div[class*='msg-out']",
            "div[class*='incoming']",
            "div[class*='outgoing']"
        ]
    
    def read_messages_from_chat(self, chat_element, limit: int = 10) -> Dict[str, Any]:
        """Read messages from a specific chat (marks as read)."""
        try:
            log_with_timestamp(f"Reading messages from chat (limit: {limit})")
            
            # Click to open chat (this will mark messages as read)
            chat_element.click()
            time.sleep(2)
            
            # Extract messages
            messages = self._extract_messages_from_opened_chat(limit)
            
            # Get chat name from header
            chat_name = self._get_chat_name_from_header()
            
            return {
                "success": True,
                "chat_name": chat_name,
                "messages": messages,
                "count": len(messages),
                "status": "Messages read successfully"
            }
            
        except Exception as e:
            log_with_timestamp(f"Error reading messages from chat: {e}", "ERROR")
            return {
                "success": False,
                "error": str(e),
                "messages": [],
                "count": 0
            }
    
    def _extract_messages_from_opened_chat(self, limit: int) -> List[Dict[str, Any]]:
        """Extract messages from the currently opened chat."""
        messages = []
        
        try:
            # Wait for messages to load
            time.sleep(2)
            
            # Find message elements
            message_elements = self._find_message_elements()
            
            if not message_elements:
                log_with_timestamp("No message elements found", "WARNING")
                return messages
            
            log_with_timestamp(f"Found {len(message_elements)} message elements")
            
            # Extract messages (limit to requested number, get most recent)
            messages_to_extract = message_elements[-limit:] if limit else message_elements
            
            for i, element in enumerate(messages_to_extract):
                try:
                    message_data = self._extract_message_data(element)
                    if message_data and message_data.get("text", "").strip():
                        messages.append(message_data)
                        log_with_timestamp(f"Extracted message {i+1}: '{message_data.get('text', '')[:50]}...'")
                except Exception as e:
                    log_with_timestamp(f"Error extracting message {i+1}: {e}", "WARNING")
                    continue
            
            log_with_timestamp(f"Successfully extracted {len(messages)} messages")
            
        except Exception as e:
            log_with_timestamp(f"Error extracting messages from opened chat: {e}", "ERROR")
        
        return messages
    
    def _find_message_elements(self) -> List:
        """Find message elements using multiple strategies."""
        message_elements = []
        
        for selector in self.message_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    message_elements.extend(elements)
                    break
            except Exception as e:
                log_with_timestamp(f"Error with selector {selector}: {e}", "WARNING")
                continue
        
        return message_elements
    
    def _extract_message_data(self, element) -> Dict[str, Any]:
        """Extract data from a message element."""
        try:
            message_data = {
                "text": "",
                "sender": "Unknown",
                "timestamp": "",
                "is_from_me": False,
                "message_type": "text"
            }
            
            # Extract message text
            self._extract_message_text(element, message_data)
            
            # Extract timestamp
            self._extract_timestamp(element, message_data)
            
            # Extract sender info
            self._extract_sender_info(element, message_data)
            
            return message_data
            
        except Exception as e:
            log_with_timestamp(f"Error extracting message data: {e}", "ERROR")
            return None
    
    def _extract_message_text(self, element, message_data: Dict[str, Any]) -> None:
        """Extract message text from element."""
        text_selectors = [
            "span[data-testid='msg-text']",
            "span.selectable-text",
            "div[data-testid='msg-text']",
            "span",
            "div"
        ]
        
        for selector in text_selectors:
            try:
                text_element = element.find_element(By.CSS_SELECTOR, selector)
                text = extract_text_safely(text_element)
                if text:
                    message_data["text"] = text
                    return
            except:
                continue
        
        # Fallback to element text
        message_data["text"] = extract_text_safely(element)
    
    def _extract_timestamp(self, element, message_data: Dict[str, Any]) -> None:
        """Extract timestamp from element."""
        try:
            time_element = element.find_element(By.CSS_SELECTOR, "span[data-testid='msg-time']")
            timestamp = extract_text_safely(time_element)
            message_data["timestamp"] = timestamp
        except Exception as e:
            log_with_timestamp(f"Error extracting timestamp: {e}", "WARNING")
    
    def _extract_sender_info(self, element, message_data: Dict[str, Any]) -> None:
        """Extract sender information from element."""
        try:
            # Check if message is from me
            is_from_me = self._is_message_from_me(element)
            message_data["is_from_me"] = is_from_me
            
            if not is_from_me:
                # Try to extract sender name
                sender_name = self._extract_sender_name(element)
                message_data["sender"] = sender_name if sender_name else "Unknown"
            else:
                message_data["sender"] = "Me"
                
        except Exception as e:
            log_with_timestamp(f"Error extracting sender info: {e}", "WARNING")
            message_data["is_from_me"] = False
            message_data["sender"] = "Unknown"
    
    def _is_message_from_me(self, element) -> bool:
        """Check if message is from me."""
        try:
            # Check element class for outgoing message indicators
            element_class = element.get_attribute("class") or ""
            if "message-out" in element_class or "outgoing" in element_class:
                return True
            
            # Check for outgoing message selectors
            outgoing_selectors = [
                "[data-testid='msg-out']",
                "[data-testid='outgoing']",
                ".message-out",
                ".outgoing"
            ]
            
            for selector in outgoing_selectors:
                try:
                    if element.find_element(By.CSS_SELECTOR, selector):
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            log_with_timestamp(f"Error checking if message is from me: {e}", "WARNING")
            return False
    
    def _extract_sender_name(self, element) -> str:
        """Extract sender name from message element."""
        try:
            sender_selectors = [
                "span[data-testid='msg-sender']",
                "[data-testid='sender']",
                ".sender"
            ]
            
            for selector in sender_selectors:
                try:
                    sender_element = element.find_element(By.CSS_SELECTOR, selector)
                    sender = extract_text_safely(sender_element)
                    if sender and sender.strip():
                        return sender.strip()
                except:
                    continue
            
            return ""
            
        except Exception as e:
            log_with_timestamp(f"Error extracting sender name: {e}", "WARNING")
            return ""
    
    def _get_chat_name_from_header(self) -> str:
        """Get chat name from the chat header."""
        try:
            header_selectors = [
                "[data-testid='conversation-header'] span[title]",
                "[data-testid='conversation-header'] span",
                "header span[title]",
                "header span"
            ]
            
            for selector in header_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if text and len(text) > 0:
                                return text
                except:
                    continue
            
            return "Unknown Chat"
            
        except Exception as e:
            log_with_timestamp(f"Error getting chat name from header: {e}", "WARNING")
            return "Unknown Chat"
    
    def send_message_to_chat(self, message: str) -> Dict[str, Any]:
        """Send message to currently open chat."""
        try:
            # Find message input
            message_input = self._find_message_input()
            
            if not message_input:
                return {"success": False, "error": "Message input box not found"}
            
            log_with_timestamp("Found message input, typing message...")
            
            # Type message
            message_input.click()
            time.sleep(1)
            message_input.send_keys(message)
            time.sleep(1)
            
            # Send message
            message_input.send_keys(Keys.ENTER)
            time.sleep(2)  # Wait for message to be sent
            
            log_with_timestamp("Message sent successfully")
            
            return {
                "success": True,
                "message": "Message sent successfully",
                "text": message
            }
            
        except Exception as e:
            log_with_timestamp(f"Error sending message: {e}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def _find_message_input(self):
        """Find message input element."""
        message_input_selectors = [
            "[data-testid='conversation-compose-box-input']",
            "[data-testid='compose-box-input']",
            "div[contenteditable='true'][data-testid='conversation-compose-box-input']",
            "div[contenteditable='true']"
        ]
        
        for selector in message_input_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if is_element_displayed(element):
                        # Check if it's an input field
                        if element.tag_name == 'div' and element.get_attribute('contenteditable') == 'true':
                            return element
                        elif element.tag_name == 'input':
                            return element
            except:
                continue
        
        return None
