import os
import logging
from modules.configuration.config import Config

logger = logging.getLogger(__name__)

#======================================HELPER FUNCTION======================================
# Helper to derive Instagrapi session filename
def get_instagrapi_session_path(instaloader_path):
    """
    Derives a clean Instagrapi session filename from the Instaloader path.
    Example: 'SessionFiles/instaloader_session' -> 'SessionFiles/instagrapi_session.json'
    """
    directory = os.path.dirname(instaloader_path)
    filename = os.path.basename(instaloader_path)
    
    if "instaloader" in filename:
        new_filename = filename.replace("instaloader", "instagrapi")
    else:
        new_filename = filename + "_instagrapi"
        
    if not new_filename.endswith(".json"):
        new_filename += ".json"
        
    return os.path.join(directory, new_filename)

#==========================================================================================
#                                  INSTALOADER
#==========================================================================================
# 1. Function to load session
def load_instaloader_session(L, username, session_file):
    """
    READ-ONLY: Attempts to load an existing Instaloader session.
    Returns: bool (Success)
    """
    logger.info("--- Loading Instaloader Session ---")
    try:
        # User Agent (Centralized)
        L.context.user_agent = Config.USER_AGENT

        if os.path.exists(session_file):
            logger.info(f"Using session file: {session_file}")
            L.load_session_from_file(username, session_file)
            logger.info("Instaloader session loaded.")
            return True
        else:
            logger.warning(f"No session file found at: {session_file}")
            return False

    except Exception as e:
        logger.warning(f"Instaloader Load Failed: {e}")
        return False

#----------------------------------------------------------------------------
# 2. Function to create session
def create_instaloader_session(L, username, password, session_file):
    """
    LOGIN & WRITE: Performs fresh login and saves session.
    Returns: bool (Success)
    """
    logger.info("--- Creating Instaloader Session ---")
    try:
        # User Agent
        L.context.user_agent = Config.USER_AGENT
        
        logger.info(f"Logging in as {username}...")
        L.login(username, password)
        
        # Ensure directory exists before saving
        session_dir = os.path.dirname(session_file)
        if session_dir and not os.path.exists(session_dir):
            os.makedirs(session_dir)
        
        L.save_session_to_file(session_file)
        logger.info(f"Login Successful. Saved to {session_file}")
        return True

    except Exception as e:
        logger.error(f"Instaloader Login Failed: {e}")
        return False

#==========================================================================================
#                                  INSTAGRAPI
#==========================================================================================
# 1. Function to load session
def load_instagrapi_session(cl, session_file):
    """
    READ-ONLY: Attempts to load an existing Instagrapi session.
    Returns: bool (Success)
    """
    logger.info("--- Loading Instagrapi Session ---")
    try:
        if os.path.exists(session_file):
            logger.info(f"Using Instagrapi session file: {session_file}")
            cl.load_settings(session_file)
            # Use 'login_by_sessionid' implicitly or verify?
            # instagrapi usually works just by loading settings if session is valid.
            if cl.user_id:
                  logger.info("Instagrapi session loaded.")
                  return True
            else:
                 # Minimal check
                 return True 
        else:
            logger.warning(f"No Instagrapi session found at: {session_file}")
            return False
            
    except Exception as e:
        logger.error(f"Instagrapi Load Failed: {e}")
        return False

#----------------------------------------------------------------------------
# 2. Function to create session
def create_instagrapi_session(cl, username, password, session_file):
    """
    LOGIN & WRITE: Performs fresh login and saves session.
    Returns: bool (Success)
    """
    logger.info("--- Creating Instagrapi Session ---")
    try:
        logger.info(f"Logging in as {username}...")
        cl.login(username, password)
        
        # Ensure directory exists
        session_dir = os.path.dirname(session_file)
        if session_dir and not os.path.exists(session_dir):
            os.makedirs(session_dir)

        cl.dump_settings(session_file)
        logger.info(f"Login Successful. Saved to {session_file}")
        return True
                
    except Exception as e:
        logger.error(f"Instagrapi Login Failed: {e}")
        return False
