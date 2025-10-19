"""Authentication management for WhatsApp Personal API."""

import time
import json
import base64
import os
from pathlib import Path
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# WhatsApp Web URLs
WHATSAPP_WEB_URL = "https://web.whatsapp.com"

# QR Code selectors
QR_CODE_SELECTORS = [
    "canvas[aria-label='Scan me!']",
    "canvas[aria-label*='Scan']",
    "canvas[aria-label*='scan']",
    "canvas",
    "[data-testid='qr-code']",
    ".qr-code canvas",
    "canvas[role='img']"
]

# Authentication indicators
AUTH_INDICATORS = [
    "[data-testid='chat-list']",
    "[data-testid='side']",
    "[data-testid='chat']",
    "div[data-testid='chat-list']",
    "[aria-label*='Search']",
    "[data-testid='header']",
    "[data-testid='menu']",
    "[data-testid='app']",
    "[data-testid='sidebar']",
    "[data-testid='conversation']",
    "input[type='text']",
    "[data-testid='send']"
]

# Page load delay
PAGE_LOAD_DELAY = 5

from .utils import find_elements_by_selectors, is_element_displayed, log_with_timestamp


class AuthenticationManager:
    """Manages WhatsApp Web authentication and session persistence."""
    
    def __init__(self, driver, session_data_path: str):
        """Initialize authentication manager."""
        self.driver = driver
        self.session_data_path = session_data_path
        self.session_data = self._load_session_data()
        self.is_authenticated = False
    
    def _load_session_data(self) -> dict:
        """Load session data from file."""
        try:
            if Path(self.session_data_path).exists():
                with open(self.session_data_path, 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            log_with_timestamp(f"Could not load session data: {e}", "WARNING")
        return {}
    
    def _save_session_data(self) -> None:
        """Save session data to file."""
        try:
            Path(self.session_data_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_data_path, 'w') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception as e:
            log_with_timestamp(f"Could not save session data: {e}", "WARNING")
    
    def start_session(self) -> dict:
        """Start WhatsApp Web session."""
        try:
            log_with_timestamp("Starting WhatsApp Web session...")
            
            # Navigate to WhatsApp Web
            self.driver.get(WHATSAPP_WEB_URL)
            log_with_timestamp("Navigated to WhatsApp Web")
            
            time.sleep(PAGE_LOAD_DELAY)
            
            # Check if already authenticated
            if self._check_already_authenticated():
                return self._handle_already_authenticated()
            
            # Check for QR code
            return self._handle_qr_code_flow()
            
        except Exception as e:
            log_with_timestamp(f"Error starting WhatsApp session: {e}", "ERROR")
            return {
                "success": False, 
                "error": str(e),
                "status": "error"
            }
    
    def _check_already_authenticated(self) -> bool:
        """Check if already authenticated by looking for chat list."""
        try:
            chat_list = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='chat-list']")
            return chat_list and is_element_displayed(chat_list)
        except:
            return False
    
    def _handle_already_authenticated(self) -> dict:
        """Handle case where user is already authenticated."""
        self.is_authenticated = True
        log_with_timestamp("Already authenticated - session restored")
        
        # Update session data
        self.session_data['authenticated'] = True
        self.session_data['last_login'] = datetime.now().isoformat()
        self.session_data['auto_restored'] = True
        self._save_session_data()
        
        return {
            "success": True, 
            "message": "Session already authenticated and restored", 
            "status": "authenticated"
        }
    
    def _handle_qr_code_flow(self) -> dict:
        """Handle QR code authentication flow."""
        log_with_timestamp("Checking for QR code...")
        time.sleep(3)
        
        qr_element = self._find_qr_code()
        
        if qr_element:
            log_with_timestamp("QR code found and ready for scanning")
            return {
                "success": True, 
                "message": "QR code ready for scanning", 
                "status": "qr_ready",
                "qr_code_available": True,
                "current_url": self.driver.current_url
            }
        else:
            return self._handle_qr_not_found()
    
    def _find_qr_code(self):
        """Find QR code element."""
        for selector in QR_CODE_SELECTORS:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if is_element_displayed(element):
                        # Check if it's actually a QR code
                        if self._is_valid_qr_code(element):
                            log_with_timestamp(f"QR code found with selector: {selector}")
                            return element
            except Exception as e:
                log_with_timestamp(f"Error checking selector {selector}: {e}", "WARNING")
                continue
        return None
    
    def _is_valid_qr_code(self, element) -> bool:
        """Check if element is a valid QR code."""
        try:
            size = element.size
            return size['width'] > 50 and size['height'] > 50
        except Exception:
            return False
    
    def _handle_qr_not_found(self) -> dict:
        """Handle case where QR code is not found."""
        log_with_timestamp("QR code not found, checking page state...", "WARNING")
        
        page_title = self.driver.title
        current_url = self.driver.current_url
        
        log_with_timestamp(f"Page title: {page_title}")
        log_with_timestamp(f"Current URL: {current_url}")
        
        if "web.whatsapp.com" in current_url:
            return {
                "success": True, 
                "message": "WhatsApp Web loaded, waiting for QR code", 
                "status": "loading",
                "page_title": page_title,
                "current_url": current_url
            }
        else:
            return {
                "success": False, 
                "error": f"Failed to load WhatsApp Web. Current URL: {current_url}",
                "status": "error"
            }
    
    def get_qr_code(self) -> dict:
        """Get QR code image from WhatsApp Web."""
        try:
            if not self.driver:
                return {"error": "No active session. Please start a session first."}
            
            # Navigate to WhatsApp Web if not already there
            if "web.whatsapp.com" not in self.driver.current_url:
                self.driver.get(WHATSAPP_WEB_URL)
                time.sleep(3)
            
            log_with_timestamp("Looking for QR code...")
            
            qr_element = self._find_qr_code()
            
            if qr_element:
                return self._capture_qr_code(qr_element)
            else:
                return self._qr_code_not_found_response()
                
        except Exception as e:
            log_with_timestamp(f"Error getting QR code: {e}", "ERROR")
            return {"success": False, "error": str(e)}
    
    def _capture_qr_code(self, qr_element) -> dict:
        """Capture QR code as base64 image."""
        try:
            qr_filename = f"qr_code_{int(time.time())}.png"
            qr_element.screenshot(qr_filename)
            log_with_timestamp(f"QR code screenshot saved: {qr_filename}")
            
            # Read and convert to base64
            with open(qr_filename, "rb") as image_file:
                qr_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Clean up temporary file
            os.remove(qr_filename)
            
            return {
                "success": True,
                "qr_code": f"data:image/png;base64,{qr_base64}",
                "message": "QR code captured successfully"
            }
            
        except Exception as e:
            log_with_timestamp(f"Error processing QR code image: {e}", "ERROR")
            return {"success": False, "error": f"Error processing QR code: {e}"}
    
    def _qr_code_not_found_response(self) -> dict:
        """Return response when QR code is not found."""
        log_with_timestamp("QR code not found", "WARNING")
        return {
            "success": False,
            "error": "QR code not found. Session might already be authenticated or WhatsApp Web is still loading.",
            "current_url": self.driver.current_url,
            "page_title": self.driver.title
        }
    
    def check_authentication_status(self) -> bool:
        """Check if WhatsApp Web is currently authenticated."""
        try:
            if not self.driver:
                log_with_timestamp("No WebDriver instance available", "ERROR")
                return False
            
            # Check if we're on WhatsApp Web
            if "web.whatsapp.com" not in self.driver.current_url:
                log_with_timestamp("Not on WhatsApp Web page", "ERROR")
                return False
            
            log_with_timestamp(f"Checking authentication status on: {self.driver.current_url}")
            time.sleep(5)  # Wait longer for page to fully load
            
            # Check for strong authentication indicators
            strong_auth_found = self._check_strong_auth_indicators()
            
            # Only check for QR code if we didn't find strong indicators
            qr_code_present = False
            if not strong_auth_found:
                qr_code_present = self._check_qr_code_present()
            
            # Final determination
            is_authenticated = strong_auth_found and not qr_code_present
            
            log_with_timestamp(f"Authentication check results: {is_authenticated}")
            return is_authenticated
            
        except Exception as e:
            log_with_timestamp(f"Error checking authentication status: {e}", "ERROR")
            return False
    
    def _check_strong_auth_indicators(self) -> bool:
        """Check for strong authentication indicators."""
        log_with_timestamp("Checking for strong authentication indicators...")
        
        # First, let's check what elements are actually present on the page
        try:
            all_elements = self.driver.find_elements(By.CSS_SELECTOR, "*")
            log_with_timestamp(f"Total elements on page: {len(all_elements)}")
            
            # Check for any elements with data-testid
            testid_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid]")
            log_with_timestamp(f"Elements with data-testid: {len(testid_elements)}")
            for elem in testid_elements[:10]:  # Show first 10
                try:
                    testid = elem.get_attribute("data-testid")
                    log_with_timestamp(f"Found data-testid: {testid}")
                except:
                    pass
        except Exception as e:
            log_with_timestamp(f"Error checking page elements: {e}", "WARNING")
        
        for indicator in AUTH_INDICATORS:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                log_with_timestamp(f"Found {len(elements)} elements for selector: {indicator}")
                for i, element in enumerate(elements):
                    if is_element_displayed(element):
                        log_with_timestamp(f"Strong authentication indicator found: {indicator} (element {i})")
                        return True
            except Exception as e:
                log_with_timestamp(f"Error checking indicator {indicator}: {e}", "WARNING")
                continue
        log_with_timestamp("No strong authentication indicators found")
        return False
    
    def _check_qr_code_present(self) -> bool:
        """Check if QR code is still present."""
        for qr_selector in QR_CODE_SELECTORS:
            try:
                qr_elements = self.driver.find_elements(By.CSS_SELECTOR, qr_selector)
                for qr_element in qr_elements:
                    if is_element_displayed(qr_element):
                        # Additional validation for QR code
                        if self._is_valid_qr_code(qr_element):
                            aria_label = qr_element.get_attribute('aria-label') or ''
                            if 'scan' in aria_label.lower() or 'qr' in aria_label.lower():
                                log_with_timestamp(f"QR code still present: {qr_selector}", "WARNING")
                                return True
            except Exception as e:
                log_with_timestamp(f"Error checking QR selector {qr_selector}: {e}", "WARNING")
                continue
        return False
    
    def get_status(self) -> dict:
        """Get authentication status."""
        try:
            actual_auth_status = self.check_authentication_status()
            
            # Update internal flag if status changed
            if actual_auth_status != self.is_authenticated:
                self.is_authenticated = actual_auth_status
                if actual_auth_status:
                    log_with_timestamp("WhatsApp authentication detected!")
                    self._update_session_data_on_auth()
                else:
                    log_with_timestamp("WhatsApp authentication lost", "WARNING")
                    self._update_session_data_on_auth_lost()
            
            return {
                "service": "whatsapp_personal",
                "authenticated": actual_auth_status,
                "status": "ready" if actual_auth_status else "not_authenticated",
                "current_url": self.driver.current_url if self.driver else None,
                "session_data_path": self.session_data_path,
                "session_info": self._get_session_info(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log_with_timestamp(f"Error getting status: {e}", "ERROR")
            return {
                "service": "whatsapp_personal",
                "authenticated": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _update_session_data_on_auth(self) -> None:
        """Update session data when authenticated."""
        self.session_data['authenticated'] = True
        self.session_data['last_login'] = datetime.now().isoformat()
        self.session_data['status_check'] = datetime.now().isoformat()
        self._save_session_data()
    
    def _update_session_data_on_auth_lost(self) -> None:
        """Update session data when authentication is lost."""
        self.session_data['authenticated'] = False
        self.session_data['auth_lost'] = datetime.now().isoformat()
        self._save_session_data()
    
    def _get_session_info(self) -> dict:
        """Get session information."""
        return {
            "authenticated": self.session_data.get('authenticated', False),
            "last_login": self.session_data.get('last_login'),
            "last_activity": self.session_data.get('last_activity'),
            "restored": self.session_data.get('restored', False),
            "restore_failed": self.session_data.get('restore_failed'),
            "expired": self.session_data.get('expired'),
            "restore_error": self.session_data.get('restore_error')
        }
