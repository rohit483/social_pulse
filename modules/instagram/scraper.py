import instaloader
import logging
import os
import time
from instagrapi import Client
from modules.configuration.config import Config

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce verbosity of instagrapi library
logging.getLogger("instagrapi").setLevel(logging.WARNING)
logging.getLogger("private_request").setLevel(logging.WARNING)

#==================================== InstagramScraper Class =================================
class InstagramScraper:
    def __init__(self):
        # 1. Initialize Instaloader (Primary)
        self.L = instaloader.Instaloader()
        self.L.context.user_agent = 'Instagram 123.0.0.26.121 Android (28/9; 320dpi; 720x1280; Xiaomi; Redmi Note 7; lavender; qcom; en_US)'
        
        # 2. Initialize Instagrapi (Fallback)
        self.cl = Client()
        
        # 3. State to track which method is active/logged in
        self.instaloader_active = False
        self.instagrapi_active = False
        
        # 4. Setup session
        self.setup_session()

#---------------------------------------------------------------------------------
# 1. Function to setup session
    def setup_session(self):
        """
        Hybrid Session Setup:
        Tries Instaloader first. If that fails, marks it as inactive.
        Instagrapi is NOT initialized here to save time, unless Instaloader fails immediately.
        """
        self._init_instaloader_session()
        
        # If Instaloader failed right out of the gate, try Instagrapi
        if not self.instaloader_active:
             self._init_instagrapi_session()

        if not self.instaloader_active and not self.instagrapi_active:
            logger.error("CRITICAL: All login methods failed.")

#---------------------------------------------------------------------------------
# 2. Function to initialize Instaloader session
    def _init_instaloader_session(self):
        username = Config.INSTAGRAM_USERNAME
        password = Config.INSTAGRAM_PASSWORD
        session_file = Config.SESSION_FILE
        
        logger.info("--- Attempting Primary Login (Instaloader) ---")
        try:
            if os.path.exists(session_file):
                logger.info(f"Loading Instaloader session from {session_file}...")
                self.L.load_session_from_file(username, session_file)
                self.instaloader_active = True
                logger.info("Instaloader session loaded.")
            else:
                 logger.info("No Instaloader session file found. Attempting direct login...")
                 self.L.login(username, password)
                 self.L.save_session_to_file(session_file)
                 self.instaloader_active = True
                 logger.info("Instaloader Login Successful.")
                 
                 # WARMUP session
                 self.warm_up_session(username)

        except Exception as e:
            logger.warning(f"Instaloader Login Failed: {e}")
            self.instaloader_active = False

#---------------------------------------------------------------------------------
# 3. Function to initialize Instagrapi session
    def _init_instagrapi_session(self):
        username = Config.INSTAGRAM_USERNAME
        password = Config.INSTAGRAM_PASSWORD
        session_file = Config.SESSION_FILE
        instagrapi_session_file = session_file.replace(".pkl", "") + "_instagrapi.json"
        
        logger.info("--- Attempting Fallback Login (Instagrapi) ---")
        try:
             if os.path.exists(instagrapi_session_file):
                 logger.info(f"Loading Instagrapi session from {instagrapi_session_file}...")
                 self.cl.load_settings(instagrapi_session_file)
                 self.cl.login(username, password)
                 self.instagrapi_active = True
                 logger.info("Instagrapi session loaded and verified.")
             else:
                 logger.info("Attempting fresh Instagrapi login...")
                 self.cl.login(username, password)
                 self.cl.dump_settings(instagrapi_session_file)
                 self.instagrapi_active = True
                 logger.info("Instagrapi Login Successful.")
                 
        except Exception as e:
             logger.error(f"Instagrapi Fallback Failed: {e}")
             self.instagrapi_active = False

#---------------------------------------------------------------------------------
# 4. Function to warm up session
    def warm_up_session(self, username):
        try:
            logger.info("Warming up Instaloader session...")
            instaloader.Profile.from_username(self.L.context, username)
            time.sleep(2)
            logger.info("Session warmed up.")
        except Exception as e:
            logger.warning(f"Warmup warning: {e}")

#---------------------------------------------------------------------------------
# 5. Function to scrape comments
    def scrape_comments(self, shortcode):
        """
        Hybrid Scraping:
        1. Try Instaloader.
        2. If it fails (login required/connection), try Instagrapi.
        """
        comments = []
        
        # --- Attempt 1: Instaloader ---
        if self.instaloader_active:
            try:
                logger.info(f"Scraping {shortcode} using Instaloader...")
                post = instaloader.Post.from_shortcode(self.L.context, shortcode)
                for comment in post.get_comments():
                    comments.append({
                        "username": comment.owner.username,
                        "comment": comment.text
                    })
                    if len(comments) >= Config.MAX_COMMENTS:
                        break
                logger.info(f"Instaloader scraped {len(comments)} comments.")
                return comments
            except Exception as e:
                logger.warning(f"Instaloader failed: {e}. Switching to Fallback...")
                self.instaloader_active = False # Mark as dead
        
        # --- Attempt 2: Instagrapi (Fallback) ---
        if not self.instagrapi_active:
             try:
                 # DIRECTLY call the specific init method, avoid the setup_session loop
                 self._init_instagrapi_session()
                 if not self.instagrapi_active:
                     raise Exception("Instagrapi failed to initialize.")
             except Exception as e:
                 logger.error(f"Could not activate fallback: {e}")
                 # Critical failure if both fail
                 if not self.instaloader_active: 
                     raise e
                 
        if self.instagrapi_active:
            try:
                logger.info(f"Scraping {shortcode} using Instagrapi (Fallback)...")
                media_pk = self.cl.media_pk_from_code(shortcode)
                amount = Config.MAX_COMMENTS if hasattr(Config, 'MAX_COMMENTS') else 50
                comments_objs = self.cl.media_comments(media_pk, amount=amount)
                
                for comment in comments_objs:
                    comments.append({
                        "username": comment.user.username,
                        "comment": comment.text
                    })
                logger.info(f"Instagrapi scraped {len(comments)} comments.")
                return comments
            except Exception as e:
                 logger.error(f"Instagrapi also failed: {e}")
                 raise e
        
        return []
