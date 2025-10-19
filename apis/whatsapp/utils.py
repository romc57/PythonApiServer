"""Utility functions for WhatsApp Personal API."""

import time
import hashlib
import urllib.parse
from typing import Dict, Any, List, Optional
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# UI text to skip when extracting chat names
SKIP_WORDS = [
    'search', 'start', 'new', 'chat', 'all', 'unread', 
    'favorites', 'groups', 'archived'
]

# Default timeout
DEFAULT_TIMEOUT = 20


def normalize_chat_name(chat_name: str) -> str:
    """Normalize chat name for consistent mapping (handles Hebrew and English)."""
    if not chat_name:
        return ""
    # Remove extra whitespace and convert to lowercase for consistent mapping
    normalized = chat_name.strip().lower()
    # For Hebrew text, we keep it as is since Hebrew doesn't have case
    return normalized


def extract_contact_name_from_text(chat_text: str) -> Optional[str]:
    """Extract contact name from chat element text."""
    if not chat_text or len(chat_text) <= 5:
        return None
    
    lines = chat_text.split('\n')
    
    # Look for contact names (skip common UI elements)
    for line in lines:
        line = line.strip()
        if (len(line) > 2 and 
            not any(skip in line.lower() for skip in SKIP_WORDS) and
            (not line.startswith('+') or line.startswith('+972'))):  # Include phone numbers
            return line
    
    return None


def wait_for_element(driver, by: By, value: str, timeout: int = DEFAULT_TIMEOUT):
    """Wait for element with timeout."""
    try:
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))
    except TimeoutException:
        raise Exception(f"Element not found: {value}")


def wait_for_clickable(driver, by: By, value: str, timeout: int = DEFAULT_TIMEOUT):
    """Wait for clickable element with timeout."""
    try:
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.element_to_be_clickable((by, value)))
    except TimeoutException:
        raise Exception(f"Element not clickable: {value}")


def safe_click(driver, element, max_retries: int = 3) -> bool:
    """Safely click element with retry logic."""
    for attempt in range(max_retries):
        try:
            driver.execute_script("arguments[0].click();", element)
            time.sleep(0.5)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            print(f"Failed to click element after {max_retries} attempts: {e}")
            return False
    return False


def safe_send_keys(element, text: str, max_retries: int = 3) -> bool:
    """Safely send keys to element with retry logic."""
    for attempt in range(max_retries):
        try:
            element.clear()
            element.send_keys(text)
            time.sleep(0.5)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            print(f"Failed to send keys after {max_retries} attempts: {e}")
            return False
    return False


def generate_chat_id(chat_name: str) -> str:
    """Generate a unique chat ID from chat name."""
    return hashlib.md5(chat_name.encode('utf-8')).hexdigest()


def parse_timestamp(timestamp: str) -> Dict[str, str]:
    """Parse WhatsApp timestamp to extract day and hour."""
    result = {"day": "Today", "hour": ""}
    
    if not timestamp:
        return result
    
    # Common WhatsApp timestamp formats: "HH:MM", "DD/MM/YY HH:MM", "Yesterday HH:MM"
    if ":" in timestamp:
        time_part = timestamp.split(" ")[-1] if " " in timestamp else timestamp
        if ":" in time_part:
            hour_min = time_part.split(":")
            result["hour"] = hour_min[0]
    
    # Extract day info
    if "Yesterday" in timestamp:
        result["day"] = "Yesterday"
    elif "/" in timestamp:
        day_part = timestamp.split(" ")[0]
        result["day"] = day_part
    
    return result


def decode_url_encoded_text(text: str) -> str:
    """Decode URL-encoded text, especially for Hebrew characters."""
    if not text:
        return text
    try:
        return urllib.parse.unquote(text)
    except Exception:
        return text


def is_element_displayed(element) -> bool:
    """Check if element is displayed safely."""
    try:
        return element and element.is_displayed()
    except Exception:
        return False


def extract_text_safely(element) -> str:
    """Extract text from element safely."""
    try:
        return element.text.strip() if element else ""
    except Exception:
        return ""


def get_element_attribute_safely(element, attribute: str) -> str:
    """Get element attribute safely."""
    try:
        return element.get_attribute(attribute) or ""
    except Exception:
        return ""


def find_elements_by_selectors(driver, selectors: List[str]) -> List:
    """Find elements using multiple selectors."""
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                return elements
        except Exception:
            continue
    return []


def find_element_by_selectors(driver, selectors: List[str]):
    """Find first element using multiple selectors."""
    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            if element and is_element_displayed(element):
                return element
        except Exception:
            continue
    return None


def create_message_data(text: str = "", sender: str = "", timestamp: str = "", 
                       is_from_me: bool = False) -> Dict[str, Any]:
    """Create standardized message data structure."""
    parsed_time = parse_timestamp(timestamp)
    
    return {
        "text": text,
        "sender": sender,
        "timestamp": timestamp,
        "day": parsed_time["day"],
        "hour": parsed_time["hour"],
        "is_from_me": is_from_me,
        "message_type": "text"
    }


def create_chat_info(name: str = "", unread_count: int = 0, 
                    last_message: str = "", timestamp: str = "") -> Dict[str, Any]:
    """Create standardized chat info structure."""
    return {
        "name": name,
        "unread_count": unread_count,
        "last_message": last_message,
        "timestamp": timestamp,
        "chat_id": generate_chat_id(name) if name else "",
        "element": None
    }


def log_with_timestamp(message: str, level: str = "INFO"):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def validate_chat_name(chat_name: str) -> bool:
    """Validate if chat name is meaningful."""
    if not chat_name or len(chat_name.strip()) < 2:
        return False
    
    # Check if it's not just UI text
    chat_lower = chat_name.lower()
    return not any(skip_word in chat_lower for skip_word in SKIP_WORDS)
