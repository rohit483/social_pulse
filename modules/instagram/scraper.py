import instaloader
import logging
import os
import time
from instagrapi import Client
from modules.configuration.config import Config
from modules.instagram.auth import load_instaloader_session, load_instagrapi_session, get_instagrapi_session_path, create_instaloader_session, create_instagrapi_session

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
        session_file = Config.SESSION_FILE
        
        self.instaloader_active = load_instaloader_session(self.L, username, session_file)
        
        if not self.instaloader_active and getattr(Config, 'ALLOW_DIRECT_LOGIN', False) and username and Config.INSTAGRAM_PASSWORD:
            logger.info("Session load failed, attempting direct login for Instaloader...")
            self.instaloader_active = create_instaloader_session(self.L, username, Config.INSTAGRAM_PASSWORD, session_file)
        
        if self.instaloader_active:
             self.warm_up_session(username)

#---------------------------------------------------------------------------------
# 3. Function to initialize Instagrapi session
    def _init_instagrapi_session(self):
        username = Config.INSTAGRAM_USERNAME
        session_file = Config.SESSION_FILE
        instagrapi_session_file = get_instagrapi_session_path(session_file)
        
        self.instagrapi_active = load_instagrapi_session(self.cl, instagrapi_session_file)

        if not self.instagrapi_active and getattr(Config, 'ALLOW_DIRECT_LOGIN', False) and username and Config.INSTAGRAM_PASSWORD:
            logger.info("Session load failed, attempting direct login for Instagrapi...")
            self.instagrapi_active = create_instagrapi_session(self.cl, username, Config.INSTAGRAM_PASSWORD, instagrapi_session_file)

#---------------------------------------------------------------------------------
# 4. Function to warm up session
    def warm_up_session(self, username, retry=True):
        try:
            logger.info("Warming up Instaloader session...")
            instaloader.Profile.from_username(self.L.context, username)
            time.sleep(2)
            logger.info("Session warmed up.")
            return True
        except Exception as e:
            logger.warning(f"Warmup warning/failure: {e}")
            self.instaloader_active = False
            if retry and getattr(Config, 'ALLOW_DIRECT_LOGIN', False):
                logger.info("Session dead during warmup. Attempting self-healing...")
                if os.path.exists(Config.SESSION_FILE):
                     os.remove(Config.SESSION_FILE)
                self._init_instaloader_session()
                return self.instaloader_active
            return False

    def warm_up_all_sessions(self):
        """Called by background APScheduler to periodically test & refresh sessions."""
        logger.info("=== Running Background Session Warmup ===")
        if self.instaloader_active:
            self.warm_up_session(Config.INSTAGRAM_USERNAME, retry=True)
        else:
            self._init_instaloader_session()
            
        if not self.instagrapi_active:
            self._init_instagrapi_session()
        else:
            try:
                 self.cl.get_timeline_feed()
                 logger.info("Instagrapi Session warmed up.")
            except Exception as e:
                 logger.warning(f"Instagrapi warmup failed: {e}. Healing...")
                 self.instagrapi_active = False
                 if getattr(Config, 'ALLOW_DIRECT_LOGIN', False):
                     instagrapi_session_file = get_instagrapi_session_path(Config.SESSION_FILE)
                     if os.path.exists(instagrapi_session_file):
                         os.remove(instagrapi_session_file)
                     self._init_instagrapi_session()

#---------------------------------------------------------------------------------
# 5. Function to scrape comments
    def scrape_comments(self, shortcode, retry=True):
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
                logger.warning(f"Instaloader failed: {e}.")
                self.instaloader_active = False # Mark as dead
                
                # --- Self-Healing ---
                if retry and getattr(Config, 'ALLOW_DIRECT_LOGIN', False):
                    logger.info("Instaloader session may be expired. Attempting self-healing...")
                    if os.path.exists(Config.SESSION_FILE):
                        os.remove(Config.SESSION_FILE)
                    self._init_instaloader_session()
                    if self.instaloader_active:
                        logger.info("Self-healing successful. Retrying scrape...")
                        return self.scrape_comments(shortcode, retry=False)
        
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
                 self.instagrapi_active = False
                 
                 # --- Self-Healing ---
                 if retry and getattr(Config, 'ALLOW_DIRECT_LOGIN', False):
                     logger.info("Instagrapi session may be expired. Attempting self-healing...")
                     instagrapi_session_file = get_instagrapi_session_path(Config.SESSION_FILE)
                     if os.path.exists(instagrapi_session_file):
                         os.remove(instagrapi_session_file)
                     self._init_instagrapi_session()
                     if self.instagrapi_active:
                         logger.info("Self-healing successful. Retrying scrape...")
                         return self.scrape_comments(shortcode, retry=False)
                 
                 raise e
        
        return []
