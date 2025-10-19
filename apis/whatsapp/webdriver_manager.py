"""WebDriver management for WhatsApp Personal API."""

import os
import time
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait

# Chrome options for WhatsApp Web
CHROME_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor",
    "--disable-extensions",
    "--disable-plugins",
    "--window-size=1920,1080",
    "--disable-blink-features=AutomationControlled",
    "--disable-logging",
    "--disable-notifications",
    "--disable-popup-blocking",
    "--disable-translate",
    "--disable-sync",
    "--disable-background-networking",
    "--disable-component-extensions-with-background-pages",
    "--disable-client-side-phishing-detection",
    "--disable-hang-monitor",
    "--disable-prompt-on-repost",
    "--disable-domain-reliability",
    "--disable-features=TranslateUI"
]

# Chrome preferences
CHROME_PREFS = {
    "profile.default_content_setting_values.cookies": 1,
    "profile.default_content_setting_values.javascript": 1,
    "profile.default_content_setting_values.plugins": 1,
    "profile.default_content_setting_values.popups": 0,
    "profile.default_content_setting_values.geolocation": 2,
    "profile.default_content_setting_values.notifications": 2,
    "profile.default_content_setting_values.media_stream": 2,
    "profile.default_content_setting_values.camera": 2,
    "profile.default_content_setting_values.microphone": 2,
    "profile.managed_default_content_settings.images": 2,
}

# Timeouts and delays
DEFAULT_TIMEOUT = 20

from .utils import log_with_timestamp


class WebDriverManager:
    """Manages Chrome WebDriver instance for WhatsApp Web."""
    
    def __init__(self, session_data_path: str, headless: bool = False):
        """Initialize WebDriver manager."""
        self.session_data_path = session_data_path
        self.headless = headless
        self.driver = None
        self.wait = None
        self.is_docker = os.path.exists('/.dockerenv')
    
    def setup_driver(self) -> None:
        """Setup Chrome WebDriver with WhatsApp Web optimized settings."""
        if self.driver:
            return
        
        self._cleanup_chrome_processes()
        
        # Try multiple times with different profile strategies
        max_retries = 3
        for attempt in range(max_retries):
            try:
                chrome_options = self._create_chrome_options(attempt)
                driver_path = self._get_chromedriver_path()
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.wait = WebDriverWait(self.driver, DEFAULT_TIMEOUT)
                
                self._hide_automation_indicators()
                print("✅ Chrome WebDriver initialized successfully")
                return
                
            except Exception as e:
                log_with_timestamp(f"Attempt {attempt + 1} failed: {e}", "WARNING")
                if attempt < max_retries - 1:
                    # Try with a different profile strategy
                    time.sleep(2)
                    continue
                else:
                    self._handle_driver_error(e)
    
    def _create_chrome_options(self, attempt: int = 0) -> Options:
        """Create Chrome options for WhatsApp Web."""
        chrome_options = Options()
        
        # Different strategies based on attempt number
        if attempt == 0:
            # First attempt: Try to use cached profile with better conflict resolution
            try:
                user_data_dir = self._get_user_data_dir()
                chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
                log_with_timestamp(f"Attempt {attempt + 1}: Using cached Chrome profile: {user_data_dir}")
            except Exception as e:
                log_with_timestamp(f"Attempt {attempt + 1}: Could not use cached profile: {e}", "WARNING")
                # Fallback to temporary profile
                import tempfile
                temp_profile = tempfile.mkdtemp(prefix="whatsapp_temp_")
                chrome_options.add_argument(f"--user-data-dir={temp_profile}")
                log_with_timestamp(f"Attempt {attempt + 1}: Using temporary profile: {temp_profile}")
        
        elif attempt == 1:
            # Second attempt: Try to copy cached profile to a new location
            try:
                import shutil
                import tempfile
                from pathlib import Path
                
                # Get the cached profile path
                auth_dir = Path(self.session_data_path).parent
                simple_profile = auth_dir / "whatsapp_chrome_profile"
                
                if simple_profile.exists():
                    # Copy cached profile to a new temporary location, excluding temporary files
                    temp_profile = tempfile.mkdtemp(prefix="whatsapp_cached_")
                    
                    def ignore_temp_files(dir, files):
                        # Ignore Chrome temporary files that cause copy errors
                        ignore_list = []
                        for file in files:
                            if file in ['SingletonLock', 'SingletonSocket', 'SingletonCookie', 'lockfile']:
                                ignore_list.append(file)
                        return ignore_list
                    
                    try:
                        shutil.copytree(simple_profile, temp_profile, dirs_exist_ok=True, ignore=ignore_temp_files)
                        chrome_options.add_argument(f"--user-data-dir={temp_profile}")
                        log_with_timestamp(f"Attempt {attempt + 1}: Using copied cached profile: {temp_profile}")
                    except Exception as copy_error:
                        log_with_timestamp(f"Attempt {attempt + 1}: Copy failed, using original profile: {copy_error}", "WARNING")
                        chrome_options.add_argument(f"--user-data-dir={simple_profile}")
                        log_with_timestamp(f"Attempt {attempt + 1}: Using original cached profile: {simple_profile}")
                else:
                    raise Exception("No cached profile to copy")
                    
            except Exception as e:
                log_with_timestamp(f"Attempt {attempt + 1}: Could not copy cached profile: {e}", "WARNING")
                # Fallback to temporary profile
                import tempfile
                temp_profile = tempfile.mkdtemp(prefix="whatsapp_temp_")
                chrome_options.add_argument(f"--user-data-dir={temp_profile}")
                log_with_timestamp(f"Attempt {attempt + 1}: Using temporary profile: {temp_profile}")
        
        else:
            # Third attempt: No user data directory (fresh session)
            log_with_timestamp(f"Attempt {attempt + 1}: Using fresh session (no profile)")
        
        # Add Chrome options
        for option in CHROME_OPTIONS:
            chrome_options.add_argument(option)
        
        # Set remote debugging port
        debug_port = 9222 + (os.getpid() % 1000)
        chrome_options.add_argument(f"--remote-debugging-port={debug_port}")
        chrome_options.add_argument("--remote-allow-origins=*")
        
        # Experimental options
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", CHROME_PREFS)
        
        # Headless mode
        if self.headless or self.is_docker:
            chrome_options.add_argument("--headless")
            self._setup_virtual_display()
        
        return chrome_options
    
    def _get_user_data_dir(self) -> str:
        """Get Chrome user data directory."""
        import time
        import os
        import random
        
        # Check if we're restoring an existing session
        auth_dir = Path(self.session_data_path).parent
        
        # Look for both patterns: whatsapp_chrome_profile and whatsapp_chrome_profile_*
        simple_profile = auth_dir / "whatsapp_chrome_profile"
        existing_profiles = list(auth_dir.glob("whatsapp_chrome_profile_*"))
        
        # Always create a unique profile to avoid conflicts
        timestamp = int(time.time())
        process_id = os.getpid()
        random_num = random.randint(1000, 9999)
        unique_profile_name = f"whatsapp_chrome_profile_{timestamp}_{process_id}_{random_num}"
        
        base_profile_dir = Path(self.session_data_path).parent / "whatsapp" / unique_profile_name
        
        # If we have an existing profile, copy it to the new unique location
        if simple_profile.exists():
            log_with_timestamp(f"Copying existing Chrome profile to unique location: {unique_profile_name}")
            import shutil
            
            def ignore_temp_files(dir, files):
                # Ignore Chrome temporary files that cause copy errors
                ignore_list = []
                for file in files:
                    if file in ['SingletonLock', 'SingletonSocket', 'SingletonCookie', 'lockfile']:
                        ignore_list.append(file)
                return ignore_list
            
            try:
                shutil.copytree(simple_profile, base_profile_dir, dirs_exist_ok=True, ignore=ignore_temp_files)
                log_with_timestamp(f"Successfully copied profile to: {base_profile_dir}")
            except Exception as e:
                log_with_timestamp(f"Failed to copy profile, using new profile: {e}", "WARNING")
                base_profile_dir.mkdir(parents=True, exist_ok=True)
        else:
            log_with_timestamp(f"Creating new Chrome profile: {unique_profile_name}")
            base_profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure directory permissions
        try:
            os.chmod(base_profile_dir, 0o755)
        except Exception as e:
            log_with_timestamp(f"Could not set permissions: {e}", "WARNING")
        
        print(f"✅ Using Chrome profile: {base_profile_dir.name}")
        return str(base_profile_dir)
    
    def _setup_virtual_display(self) -> None:
        """Setup virtual display for Docker."""
        if not self.is_docker:
            return
        
        try:
            subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1920x1080x24'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.environ['DISPLAY'] = ':99'
            time.sleep(2)
            print("✅ Virtual display started")
        except Exception as e:
            print(f"⚠️ Could not start virtual display: {e}")
    
    def _get_chromedriver_path(self) -> str:
        """Get ChromeDriver executable path."""
        driver_path = ChromeDriverManager().install()
        if not driver_path:
            raise Exception("ChromeDriverManager returned None")
        
        if not os.path.exists(driver_path):
            raise Exception(f"ChromeDriver not found at {driver_path}")
        
        # Handle notices file issue
        if driver_path.endswith('THIRD_PARTY_NOTICES.chromedriver'):
            driver_dir = os.path.dirname(driver_path)
            actual_driver = os.path.join(driver_dir, 'chromedriver')
            if os.path.exists(actual_driver):
                driver_path = actual_driver
            else:
                raise Exception(f"ChromeDriver binary not found in {driver_dir}")
        
        # Make executable
        os.chmod(driver_path, 0o755)
        return driver_path
    
    def _hide_automation_indicators(self) -> None:
        """Hide automation indicators from WhatsApp Web."""
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
    
    def _cleanup_chrome_processes(self) -> None:
        """Clean up Chrome processes and lock files."""
        try:
            if os.name == 'posix':
                subprocess.run(['pkill', '-f', 'chrome'], capture_output=True)
                subprocess.run(['pkill', '-f', 'chromium'], capture_output=True)
                subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
            
            self._cleanup_lock_files()
            self._cleanup_old_profiles()
            
        except Exception as e:
            log_with_timestamp(f"Could not cleanup Chrome processes: {e}", "WARNING")
    
    def _cleanup_lock_files(self) -> None:
        """Clean up old lock files."""
        base_profile_dir = Path(self.session_data_path).parent / "whatsapp_chrome_profile"
        lock_file = base_profile_dir / ".chrome_lock"
        
        if lock_file.exists():
            lock_age = time.time() - lock_file.stat().st_mtime
            if lock_age > 60:  # 1 minute timeout
                try:
                    lock_file.unlink()
                    print(f"🧹 Cleaned up old lock file (age: {lock_age:.1f}s)")
                except:
                    pass
    
    def _cleanup_old_profiles(self) -> None:
        """Clean up old unique profile directories."""
        auth_dir = Path(self.session_data_path).parent
        for profile_dir in auth_dir.glob("whatsapp_chrome_profile_*"):
            try:
                if profile_dir.is_dir():
                    dir_age = time.time() - profile_dir.stat().st_mtime
                    if dir_age > 600:  # 10 minutes
                        import shutil
                        shutil.rmtree(profile_dir)
                        print(f"🧹 Cleaned up old profile: {profile_dir.name}")
            except:
                pass
    
    def _handle_driver_error(self, error: Exception) -> None:
        """Handle WebDriver initialization errors."""
        error_msg = f"Failed to initialize Chrome WebDriver: {error}"
        
        if self.is_docker:
            error_msg += "\n\n🐳 Docker Environment Detected:"
            error_msg += "\n   • Chrome is installed in the container"
            error_msg += "\n   • Make sure to rebuild: docker compose build"
            error_msg += "\n   • Or run locally: python api_server.py"
        else:
            error_msg += "\n\n💡 Try running locally:"
            error_msg += "\n   1. Stop Docker: docker compose down"
            error_msg += "\n   2. Run locally: python api_server.py"
            error_msg += "\n   3. Access: http://localhost:8081/whatsapp/auth"
        
        raise Exception(error_msg)
    
    def quit(self) -> None:
        """Quit WebDriver and cleanup."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self._cleanup_chrome_processes()
            except Exception as e:
                log_with_timestamp(f"Error quitting WebDriver: {e}", "ERROR")
    
    def get_driver(self):
        """Get WebDriver instance."""
        return self.driver
    
    def get_wait(self):
        """Get WebDriverWait instance."""
        return self.wait
