import os
import base64
import json
import tempfile
from instagrapi import Client
from dotenv import load_dotenv

# Load from project root .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def test():
    print("=== Testing Instagrapi Session ===")
    cl = Client()
    
    session_b64 = os.environ.get('INSTAGRAPI_SESSION_B64')
    
    if session_b64:
        print("⏳ Found INSTAGRAPI_SESSION_B64 in .env, decoding...")
        try:
            decoded = base64.b64decode(session_b64).decode('utf-8')
            session_data = json.loads(decoded)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='_ig_session.json', delete=False) as tmp:
                json.dump(session_data, tmp)
                tmp_path = tmp.name
                
            try:
                cl.load_settings(tmp_path)
                print("✅ Session settings loaded successfully from Base64.")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
        except Exception as e:
            print(f"❌ Failed to decode or load session: {e}")
            return
    else:
        sp_env_path = os.path.join(os.path.dirname(__file__), '..', 'sp_env', 'session.json')
        if os.path.exists(sp_env_path):
            print(f"⏳ Found session file at {sp_env_path}, loading...")
            try:
                cl.load_settings(sp_env_path)
                print("✅ Session settings loaded successfully from disk.")
            except Exception as e:
                print(f"❌ Failed to load session from file: {e}")
                return
        else:
            print("❌ No INSTAGRAPI_SESSION_B64 in .env AND no session.json in sp_env/ found.")
            return

    # Now test if the session actually works on Instagram
    try:
        print("⏳ Testing connection by fetching user ID for 'instagram'...")
        user_id = cl.user_id_from_username("instagram")
        print(f"✅ Success! Connected. (Fetched user ID: {user_id})")
    except Exception as e:
        print(f"❌ Connection test failed! Instagram rejected the session: {e}")
        print("   This means the session is expired, invalid, or requires a challenge/login.")

if __name__ == "__main__":
    test()
