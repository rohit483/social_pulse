import os
import logging
import base64
import json
import tempfile
from modules.configuration.config import Config

logger = logging.getLogger(__name__)

#======================================HELPER FUNCTION======================================
# Helper to decode session from environment variable
def decode_session_from_env(env_var_name):
    """
    Decode session from base64 environment variable.
    Example: INSTAGRAPI_SESSION_B64
    Returns: dict (session data) or None
    """
    env_value = os.environ.get(env_var_name)
    if not env_value:
        logger.warning(f"Environment variable {env_var_name} not found")
        return None
    
    try:
        decoded = base64.b64decode(env_value).decode('utf-8')
        session_data = json.loads(decoded)
        logger.info(f"Session decoded from {env_var_name}")
        return session_data
    except Exception as e:
        logger.error(f"Failed to decode session from {env_var_name}: {e}")
        return None

#==========================================================================================
#                                  INSTALOADER
#==========================================================================================
# 1. Function to load session
def load_instaloader_session(L, username):
    """
    READ-ONLY: Attempts to load an existing Instaloader session.
    Only decodes from the INSTALOADER_SESSION_B64 environment variable.
    Returns: bool (Success)
    """
    logger.info("--- Loading Instaloader Session ---")
    try:
        L.context.user_agent = Config.USER_AGENT

        # Decode environment variable
        session_b64 = os.environ.get('INSTALOADER_SESSION_B64')
        if session_b64:
            tmp_path = None
            try:
                session_bytes = base64.b64decode(session_b64)
                with tempfile.NamedTemporaryFile(delete=False, suffix='_il_session') as tmp:
                    tmp.write(session_bytes)
                    tmp_path = tmp.name
                logger.info("Loading Instaloader session from environment variable...")
                L.load_session_from_file(username, tmp_path)
                logger.info("Instaloader session loaded from environment variable.")
                return True
            except Exception as e:
                logger.warning(f"Failed to load Instaloader session from env var: {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        logger.warning(f"No INSTALOADER_SESSION_B64 found in environment.")
        return False

    except Exception as e:
        logger.warning(f"Instaloader Load Failed: {e}")
        return False

#==========================================================================================
#                                  INSTAGRAPI
#==========================================================================================
# 1. Function to load session
def load_instagrapi_session(cl):
    """
    READ-ONLY: Attempts to load an existing Instagrapi session.
    Only decodes from the INSTAGRAPI_SESSION_B64 environment variable.
    Returns: bool (Success)
    """
    logger.info("--- Loading Instagrapi Session ---")
    try:
        # Decode environment variable
        session_from_env = decode_session_from_env('INSTAGRAPI_SESSION_B64')
        if session_from_env:
            tmp_path = None
            try:
                # Write to a proper temp file and guarantee cleanup
                with tempfile.NamedTemporaryFile(mode='w', suffix='_ig_session.json',
                                                 delete=False) as tmp:
                    json.dump(session_from_env, tmp)
                    tmp_path = tmp.name
                logger.info("Loading Instagrapi session from environment variable...")
                cl.load_settings(tmp_path)
                logger.info("Instagrapi session loaded from environment variable.")
                return True
            except Exception as e:
                logger.warning(f"Failed to load Instagrapi session from env var: {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        logger.warning("No INSTAGRAPI_SESSION_B64 found in environment.")
        return False

    except Exception as e:
        logger.error(f"Instagrapi Load Failed: {e}")
        return False


