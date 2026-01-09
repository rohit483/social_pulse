import instaloader
import logging
import os
import time
import pickle
import requests

# Import modules
from modules.configuration.config import Config

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#=======================================    Instagram Scraper Class    =======================================
# Function to initialize Instagram scraper
class InstagramScraper:
    def __init__(self):
        self.L = instaloader.Instaloader() # Initialize Instaloader
        self.L.context.user_agent = 'Instagram 123.0.0.26.121 Android (28/9; 320dpi; 720x1280; Xiaomi; Redmi Note 7; lavender; qcom; en_US)'
        self.setup_session()

#=======================================    Login Management    =======================================
# 1. Function to setup Instagram session
# Load session from file, or login via various methods. 
    def setup_session(self): #Priority: 1. File -> 2. Direct Login -> 3. Selenium Fallback -> 4. Browser Cookies Fallback
        session_file = Config.SESSION_FILE
        username = Config.INSTAGRAM_USERNAME
        password = Config.INSTAGRAM_PASSWORD
        
        logger.info(f"Initializing Instagram session for user: {username}")

        # Validate credentials before attempting login to save time
        if not username or not password:
            logger.error("CRITICAL: Instagram credentials are missing or empty. Check your .env file.")
            logger.error(f"Username: {username}, Password: {'***' if password else 'None'}")
            return

        # 1. Try loading from Session file
        if os.path.exists(session_file):
            try:
                self.L.load_session_from_file(username, session_file)
                logger.info("Loaded session from file.")
                
                # Verify if session is actually valid
                if self.validate_session(username):
                    return
                else:
                    logger.warning("Session loaded but invalid. Attempting to re-login.")

            # Exception handling for file loading     
            except Exception as e:
                logger.warning(f"Failed to load session: {e}")

        # 2. Try Direct Login
        try:
            logger.info("Attempting direct login...")
            self.L.login(username, password)
            self.L.save_session_to_file(session_file)
            logger.info("SUCCESS: Logged in via Instaloader direct login.")
            
            # Warm up the session to prevent first-request errors
            self.warm_up_session(username)
            return

        # Exception handling for direct login     
        except Exception as e:
             logger.warning(f"Direct login method failed (trying Selenium fallback): {e}")

        # 3. Selenium Fallback
        logger.info("Attempting Selenium login fallback...")
        if self.selenium_login(username, password):
             logger.info("SUCCESS: Logged in via Selenium fallback.")
             
             # Warm up the session to prevent first-request errors
             self.warm_up_session(username)
             return

        # 4. Browser Cookies Fallback
        logger.info("Attempting to load cookies from browser...")
        if self.load_browser_cookies(username):
             logger.info("SUCCESS: Loaded session from browser cookies.")
             
             # Warm up the session to prevent first-request errors
             self.warm_up_session(username)
             return
        else:
             logger.error("CRITICAL: All login methods failed. Please check credentials.")

#-----------------------------------------------------------------------------------
# 2. Function to warm up a fresh session
    def warm_up_session(self, username):
        # Makes a dummy API call after fresh login to 'register' the session.
        try:
            logger.info("Warming up session with test API call...")
            
            # Make a simple query (get own profile) to activate the session
            instaloader.Profile.from_username(self.L.context, username)
            
            # Small delay to let Instagram process the request
            time.sleep(2)
            
            logger.info("Session warmed up successfully.")
        except Exception as e:
            logger.warning(f"Session warm-up encountered an issue (this is usually okay): {e}")

#-----------------------------------------------------------------------------------
# 3. Function to validate Instagram session
    def validate_session(self, username):
        try: #try to get own profile or check is_logged_in
            if not self.L.context.is_logged_in:
                return False

            # Deeper check: Query own profile
            instaloader.Profile.from_username(self.L.context, username)
            return True

        # Exception handling for session validation  
        except Exception as e:
            logger.warning(f"Session validation failed: {e}")
            return False

#-----------------------------------------------------------------------------------
# 4. Function to login via Selenium
    def selenium_login(self, username, password):
        # Importing here prevents 2-3s delay on app startup if this fallback isn't needed.
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager

        # Exception handling for selenium dependencies   
        except ImportError as e:
            logger.error(f"Selenium dependencies missing: {e}")
            return False

        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Use webdriver_manager to automatically install the correct driver
        try:
            service = Service(ChromeDriverManager().install())

        # Exception handling for webdriver_manager
        except Exception as e:
            logger.warning(f"webdriver_manager failed: {e}. Falling back to config path.")

            # Fallback to config path
            driver_path = Config.CHROME_DRIVER_PATH
            if os.path.isabs(driver_path) and os.path.exists(driver_path):
                service = Service(driver_path)
            else:
                 logger.error("No valid driver path found.")
                 return False
        
        # Initialize WebDriver
        driver = None
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get('https://www.instagram.com/accounts/login/')
            time.sleep(5)
            wait = WebDriverWait(driver, 20)
            
            # Login interactions
            user_input = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
            user_input.send_keys(username)
            pass_input = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
            pass_input.send_keys(password)
            
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
            btn.click()
            time.sleep(10)
            
            # Extract cookies and load into Instaloader
            if "login" not in driver.current_url:
                 cookies = driver.get_cookies() 
                 for cookie in cookies:
                     self.L.context._session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
                 
                 # Save session
                 self.L.save_session_to_file(Config.SESSION_FILE)
                 return True
            return False

        # Exception handling for selenium login
        except Exception as e:
            logger.error(f"Selenium login error: {e}")
            return False

        # Driver cleanup    
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

#-----------------------------------------------------------------------------------
# 5. Function to load cookies from user's browser
    def load_browser_cookies(self, username):
        # Tries Chrome, Firefox, and Edge in order.
        try:
            import browser_cookie3
            # List of browsers to try (in order of popularity)
            browsers = [
                ('Chrome', browser_cookie3.chrome),
                ('Firefox', browser_cookie3.firefox),
                ('Edge', browser_cookie3.edge)
            ]
            
            # Try each browser
            for browser_name, browser_fn in browsers:
                # Requires user to be logged into Instagram in their browser.
                try:
                    logger.info(f"Trying to load cookies from {browser_name}...")
                    
                    # Get cookies for instagram.com domain
                    cookies = browser_fn(domain_name='instagram.com')
                    
                    # Load cookies into Instaloader session
                    for cookie in cookies:
                        self.L.context._session.cookies.set(
                            cookie.name, 
                            cookie.value, 
                            domain=cookie.domain
                        )
                    
                    # Validate if the cookies work
                    if self.validate_session(username):
                        logger.info(f"Successfully loaded cookies from {browser_name}")
                        
                        # Save session for future use
                        self.L.save_session_to_file(Config.SESSION_FILE)
                        return True
                        
                # Exception handling for individual browser failures
                except Exception as browser_error:
                    logger.debug(f"{browser_name} cookie load failed: {browser_error}")
                    continue
            
            # No browser had valid cookies
            logger.warning("No valid Instagram cookies found in any browser")
            return False
            
        # Exception handling for browser_cookie3 import
        except ImportError:
            logger.warning("browser_cookie3 library not installed. Install with: pip install browser_cookie3")
            return False
        except Exception as e:
            logger.error(f"Browser cookie loading error: {e}")
            return False

#=======================================    Comment Scraping    ======================================
# 6. Function to scrape comments
    def scrape_comments(self, shortcode): 
        try:
            post = instaloader.Post.from_shortcode(self.L.context, shortcode)
            comments = []
            for comment in post.get_comments():
                comments.append({
                    "username": comment.owner.username,
                    "comment": comment.text
                })
                if len(comments) >= Config.MAX_COMMENTS:
                    break
            return comments #Returns: List of dicts {username, comment}

        # Exception handling for comment scraping    
        except Exception as e:
            logger.error(f"Error scraping {shortcode}: {e}")
            raise e
