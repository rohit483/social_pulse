import os
import logging
from dotenv import load_dotenv


#=======================================    Environment    =======================================
# Load environment variables from the root directory
load_dotenv()

#=======================================    Config    =======================================
# Config class for application configuration
class Config:
    # API Keys & Secrets
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-123'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY')

    # Base directory for the application
    BASE_DIR = os.getcwd()
    
    # Paths to CSV upload and download folders
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'webdata', 'csv uploads')
    DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER') or os.path.join(os.getcwd(), 'webdata', 'csv downloads')

    INSTAGRAM_USERNAME = os.environ.get('INSTAGRAM_USERNAME', '').strip() or None

    # User Agent
    USER_AGENT = os.environ.get('INSTAGRAM_USER_AGENT', 'Instagram 123.0.0.26.121 Android (28/9; 320dpi; 720x1280; Xiaomi; Redmi Note 7; lavender; qcom; en_US)')

    # Validation & Debugging
    _logger = logging.getLogger(__name__)

    # Validation: Log warning if credentials are missing
    if not INSTAGRAM_USERNAME:
        _logger.warning("Instagram username not found in environment variables!")
    
    # ── Session Management ─────────────────────────────────────────────────────
    # Sessions are exclusively loaded from Base64 environment variables
    # (INSTALOADER_SESSION_B64 and INSTAGRAPI_SESSION_B64). No local files are used.


    # Comment limit
    MAX_COMMENTS = 200

    # ── Database Management ────────────────────────────────────────────────────
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'user')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'password')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'social_pulse')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'db')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    #=======================================   Create directories    =======================================
    # Static method to initialize app - Create upload and download folders if they don't exist
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.DOWNLOAD_FOLDER, exist_ok=True)