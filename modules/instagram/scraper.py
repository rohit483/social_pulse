import logging
import sys

from instagrapi import Client

from modules.configuration.config import Config
from modules.instagram.auth import load_instagrapi_session

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)
logging.getLogger("instagrapi").setLevel(logging.WARNING)
logging.getLogger("private_request").setLevel(logging.WARNING)


class InstagramScraper:
    """Instagram comment scraper backed exclusively by Instagrapi."""

    def __init__(self):
        self.cl = Client()
        self.instagrapi_active = load_instagrapi_session(self.cl)

    def setup_session(self):
        self.instagrapi_active = load_instagrapi_session(self.cl)
        return self.instagrapi_active

    def scrape_comments(self, shortcode, retry=True):
        if not self.instagrapi_active:
            raise RuntimeError(
                "Instagrapi session is unavailable. Refresh INSTAGRAPI_SESSION_B64."
            )

        try:
            logger.info(f"Scraping {shortcode} using Instagrapi...")
            media_pk = self.cl.media_pk_from_code(shortcode)
            comment_objects = self.cl.media_comments(
                media_pk,
                amount=Config.MAX_COMMENTS,
            )
            comments = [
                {
                    "username": getattr(getattr(comment, "user", None), "username", "unknown"),
                    "comment": getattr(comment, "text", ""),
                }
                for comment in comment_objects
                if getattr(comment, "text", "")
            ]
            logger.info(f"Instagrapi scraped {len(comments)} comments.")
            return comments[:Config.MAX_COMMENTS]
        except Exception as error:
            self.instagrapi_active = False
            logger.warning(f"Instagrapi failed during scrape: {error}")
            raise RuntimeError(f"Instagrapi scraping failed: {error}") from error
