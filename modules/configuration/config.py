import os
from dotenv import load_dotenv

#=======================================    Environment    =======================================
# Load environment variables from common directory names
possible_env_dirs = ['sp_env', 'venv', 'env']
env_loaded = False

for env_dir in possible_env_dirs:
    env_path = os.path.join(os.getcwd(), env_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    load_dotenv() # Fallback to default .env in root

#=======================================    Config    =======================================
# Config class for application configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'

    # Base directory for the application
    BASE_DIR = os.getcwd()
    
    # Paths to CSV upload and download folders
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'webdata', 'csv uploads')
    DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER') or os.path.join(os.getcwd(), 'webdata', 'csv downloads')

    # Instagram Credentials Call from .env file
    _user = os.environ.get('INSTAGRAM_USERNAME', '').strip()
    _pass = os.environ.get('INSTAGRAM_PASSWORD', '').strip()

    # Remove accidentally included quotes (both single and double)
    INSTAGRAM_USERNAME = _user.strip("'").strip('"') if _user else None
    INSTAGRAM_PASSWORD = _pass.strip("'").strip('"') if _pass else None

    # Validation: Log warning if credentials are missing
    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        import logging
        logging.warning("Instagram credentials not found in environment variables!")
    
    # Paths to session file and chrome driver
    SESSION_FILE = os.environ.get('INSTAGRAM_SESSION_FILE') or os.path.join(BASE_DIR, 'SessionFiles', 'instaloader_session')
    CHROME_DRIVER_PATH = os.environ.get('CHROME_DRIVER_PATH') or os.path.join(BASE_DIR, 'chromedriver.exe')

    # Comment limit
    MAX_COMMENTS = 200
    
    # Static method to initialize app
    @staticmethod

#=======================================   Create directories    =======================================
    # Create upload and download folders if they don't exist
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.DOWNLOAD_FOLDER, exist_ok=True)
        
        # Ensure session directory exists
        session_dir = os.path.dirname(Config.SESSION_FILE)
        if session_dir: # Check if path is not empty
            os.makedirs(session_dir, exist_ok=True)