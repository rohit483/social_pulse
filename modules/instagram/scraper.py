import instaloader
import logging
import os
import time
import sys
from instagrapi import Client
from modules.configuration.config import Config
from modules.instagram.auth import load_instaloader_session, load_instagrapi_session

# Configure Logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Reduce verbosity of instagrapi library
logging.getLogger("instagrapi").setLevel(logging.WARNING)
logging.getLogger("private_request").setLevel(logging.WARNING)

#==================================== InstagramScraper Class =================================
class InstagramScraper:
    def __init__(self):
        # 1. Initialize Instaloader (Primary)
        # Prevent 429 rate limits from triggering infinite 30-minute sleeps that lock up Flask workers
        self.L = instaloader.Instaloader(
            max_connection_attempts=1,
            fatal_status_codes=[429, 400, 401, 403, 404, 500, 502, 503, 504]
        )
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
        Always initialises BOTH engines independently so either can act as
        fallback during scraping, regardless of which one came up healthy.
        Instagrapi is tried first; Instaloader is always attempted in parallel.
        """
        self._init_instagrapi_session()
        self._init_instaloader_session()   # always init — not just on Instagrapi failure

        if not self.instagrapi_active and not self.instaloader_active:
            logger.error("CRITICAL: All login methods failed.")

#---------------------------------------------------------------------------------
# 2. Function to initialize Instaloader session
    def _init_instaloader_session(self):
        username = Config.INSTAGRAM_USERNAME

        self.instaloader_active = load_instaloader_session(self.L, username)

#---------------------------------------------------------------------------------
# 3. Function to initialize Instagrapi session
    def _init_instagrapi_session(self):
        self.instagrapi_active = load_instagrapi_session(self.cl)

#---------------------------------------------------------------------------------
# 4. Function to scrape comments
    def scrape_comments(self, shortcode, retry=True):
        """
        Hybrid Scraping:
        1. Try Instagrapi (Primary).
        2. If it fails, try Instaloader (Fallback).
        Only self-heal if session fails DURING scraping, not if it failed during setup.
        """
        comments = []
        
        # --- Attempt 1: Instagrapi (Primary) ---
        if self.instagrapi_active:
            try:
                logger.info(f"Scraping {shortcode} using Instagrapi (Primary)...")
                media_pk = self.cl.media_pk_from_code(shortcode)
                comments_objs = self.cl.media_comments(media_pk, amount=Config.MAX_COMMENTS)
                
                for comment in comments_objs:
                    comments.append({
                        "username": comment.user.username,
                        "comment": comment.text
                    })
                logger.info(f"Instagrapi scraped {len(comments)} comments.")
                return comments
            except Exception as e:
                 logger.warning(f"Instagrapi failed during scrape: {e}.")
                 self.instagrapi_active = False
        
        if not self.instagrapi_active:
             logger.info("Primary Instagrapi is inactive. Using Fallback...")
        
        # --- Attempt 2: Instaloader (Fallback) ---
        if self.instaloader_active:
            try:
                logger.info(f"Scraping {shortcode} using Instaloader (Fallback)...")
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
                logger.warning(f"Instaloader failed during scrape: {e}.")
                self.instaloader_active = False
                raise e
        
        # --- Both inactive from setup ---
        logger.error("CRITICAL: No active session available for scraping")
        raise Exception("All scraping methods failed - no active session")
