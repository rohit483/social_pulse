import instaloader
import logging
import os
import time
from instagrapi import Client
from modules.configuration.config import Config
from modules.instagram.auth import load_instaloader_session, load_instagrapi_session, get_instagrapi_session_path

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
        # User Agent is now set inside authenticate_instaloader
        
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
        # Strict mode: No password used here.
        session_file = Config.SESSION_FILE
        
        self.instaloader_active = load_instaloader_session(self.L, username, session_file)
        
        if self.instaloader_active:
             self.warm_up_session(username)

#---------------------------------------------------------------------------------
# 3. Function to initialize Instagrapi session
    def _init_instagrapi_session(self):
        # Strict mode: No password used here.
        session_file = Config.SESSION_FILE
        instagrapi_session_file = get_instagrapi_session_path(session_file)
        
        self.instagrapi_active = load_instagrapi_session(self.cl, instagrapi_session_file)

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
        
        if not self.instaloader_active:
             logger.info("Primary Instaloader is inactive (or failed). Attempting Fallback...")
        
        # --- Attempt 2: Instagrapi ---
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
