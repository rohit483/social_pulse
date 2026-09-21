import base64
import json
import logging
import os
import tempfile

logger = logging.getLogger(__name__)


def load_instagrapi_session(client):
    """Load the Instagrapi session settings from INSTAGRAPI_SESSION_B64."""
    encoded_session = os.environ.get("INSTAGRAPI_SESSION_B64", "").strip()
    if not encoded_session:
        logger.warning("INSTAGRAPI_SESSION_B64 is not configured")
        return False

    try:
        session_data = json.loads(base64.b64decode(encoded_session).decode("utf-8"))
        with tempfile.NamedTemporaryFile(mode="w", suffix="_ig_session.json", delete=False) as handle:
            json.dump(session_data, handle)
            session_path = handle.name
        try:
            client.load_settings(session_path)
        finally:
            os.unlink(session_path)
        logger.info("Instagrapi session loaded successfully")
        return True
    except Exception as error:
        logger.warning(f"Failed to load Instagrapi session: {error}")
        return False
