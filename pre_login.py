import os
import instaloader
from instagrapi import Client
from modules.configuration.config import Config
from modules.instagram.auth import create_instaloader_session, create_instagrapi_session, get_instagrapi_session_path
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#----------------------------------------------------------------------------------
# Function to generate sessions for both Instaloader and Instagrapi
def generate_sessions():
    """
    Perform fresh logins for both Instaloader and Instagrapi
    to generate the necessary session files.
    """
    print("\n" + "="*50)
    print(" SOCIAL PULSE: SESSION GENERATOR")
    print("="*50 + "\n")


    
    username = Config.INSTAGRAM_USERNAME
    password = Config.INSTAGRAM_PASSWORD
    session_file_path = Config.SESSION_FILE
    
    # Check credentials
    if not username or not password:
        logger.error("❌ Credentials missing in .env file!")
        return

    # Debug Loading
    masked_pass = password[0] + "*" * (len(password)-2) + password[-1] if len(password) > 2 else "***"
    print(f"DEBUG: Loaded Username: {username}")
    print(f"DEBUG: Loaded Password: {masked_pass} (Length: {len(password)})")

    logger.info(f"Generating sessions for user: {username}")
    logger.info(f"Target Session Path: {session_file_path}")

    # 1. ------------------------------- Instaloader Login -------------------------------
    print("\n--- 1. Instaloader Login ---")
    L = instaloader.Instaloader()
    
    success = create_instaloader_session(L, username, password, session_file_path)
    if success:
         logger.info(f"✅ Instaloader session saved: {session_file_path}")
    else:
         logger.error("❌ Instaloader Login Failed.")

    # 2. ------------------------------- Instagrapi Login -------------------------------
    print("\n--- 2. Instagrapi Login ---")
    cl = Client()
    instagrapi_session_file = get_instagrapi_session_path(session_file_path)
    
    success_grapi = create_instagrapi_session(cl, username, password, instagrapi_session_file)
    if success_grapi:
         logger.info(f"✅ Instagrapi session saved: {instagrapi_session_file}")
    else:
         logger.error("❌ Instagrapi Login Failed.")

    print("\n" + "="*50)
    print(" DONE! Please ensure both files exist in 'SessionFiles/'")
    print("="*50 + "\n")

# ----------------------------------------------------------------------------------
if __name__ == "__main__":
    generate_sessions()
