import os
import base64
import tempfile
import instaloader
from dotenv import load_dotenv

# Load from project root .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def test():
    print("=== Testing Instaloader Session ===")
    L = instaloader.Instaloader()
    
    # Try to load from env var first (like the app does)
    session_b64 = os.environ.get('INSTALOADER_SESSION_B64')
    username = os.environ.get('INSTAGRAM_USERNAME', 'unknown')
    
    if session_b64:
        print(f"⏳ Found INSTALOADER_SESSION_B64 in .env for user '{username}', decoding...")
        try:
            session_bytes = base64.b64decode(session_b64)
            with tempfile.NamedTemporaryFile(delete=False, suffix='_il_session') as tmp:
                tmp.write(session_bytes)
                tmp_path = tmp.name
            
            try:
                L.load_session_from_file(username, tmp_path)
                print("✅ Session file loaded successfully from Base64.")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
        except Exception as e:
            print(f"❌ Failed to decode or load session: {e}")
            return
    else:
        # Check if the user placed it in sp_env directly
        sp_env_path = os.path.join(os.path.dirname(__file__), '..', 'sp_env', f'session-{username}')
        if os.path.exists(sp_env_path):
            print(f"⏳ Found session file at {sp_env_path}, loading...")
            try:
                L.load_session_from_file(username, sp_env_path)
                print("✅ Session file loaded successfully from disk.")
            except Exception as e:
                print(f"❌ Failed to load session from file: {e}")
                return
        else:
            print("❌ No INSTALOADER_SESSION_B64 in .env AND no session file found.")
            print(f"   (Looking for sp_env/session-{username})")
            return

    # Now test if the session actually works on Instagram
    try:
        print("⏳ Testing connection by fetching a profile...")
        profile = instaloader.Profile.from_username(L.context, "instagram")
        print(f"✅ Success! Connected. (Fetched profile: {profile.username})")
    except Exception as e:
        print(f"❌ Connection test failed! Instagram rejected the session: {e}")
        print("   This means the session is expired, invalid, or requires a challenge/login.")

if __name__ == "__main__":
    test()
