import os
import json
import base64
import instaloader
from instagrapi import Client
from dotenv import load_dotenv

# Load variables from .env if present
load_dotenv()

# Read username from .env (fallback to devritzloper)
USERNAME = os.environ.get("INSTAGRAM_USERNAME", "devritzloper")

def _write_env_var(key: str, value: str, env_path: str = '.env'):
    """Helper to update .env variables safely."""
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    key_found = False
    new_lines = []
    for line in lines:
        if line.startswith(f'{key}=') or line.startswith(f'{key} ='):
            new_lines.append(f'{key}={value}\n')
            key_found = True
        else:
            new_lines.append(line)

    if not key_found:
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines.append('\n')
        new_lines.append(f'{key}={value}\n')

    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


def generate_from_json():
    print("="*50)
    print(f" [>] EXTRACTING FROM COOKIE.JSON")
    print("="*50)
    
    # ---------------------------------------------------------
    # 1. READ EXPORTED COOKIES
    # ---------------------------------------------------------
    if not os.path.exists('cookie.json'):
        print(" [!] Error: 'cookie.json' file not found in this folder.")
        print("Please export your cookies from Chrome and save them as 'cookie.json'.")
        return

    try:
        with open('cookie.json', 'r', encoding='utf-8') as f:
            raw_cookies = json.load(f)
            
        if not raw_cookies:
            print(" [!] cookie.json is empty. Skipping session extraction.")
            return
            
        # Format the extension data into a simple dictionary
        cookie_dict = {}
        for cookie in raw_cookies:
            # Handle different extension formats ('name' vs 'id')
            name = cookie.get('name', cookie.get('id', ''))
            value = cookie.get('value', '')
            if name and value:
                cookie_dict[name] = value
                
        if 'sessionid' not in cookie_dict:
            print(" [!] Error: No 'sessionid' found in the JSON file. Are you sure you exported Instagram cookies?")
            return
            
        print(f" [+] Loaded {len(cookie_dict)} cookies from JSON successfully!")
        
    except Exception as e:
        print(f" [!] Failed to parse cookie.json: {e}")
        return

    # ---------------------------------------------------------
    # 2. GENERATE INSTAGRAPI BASE64
    # ---------------------------------------------------------
    print("\n[1/2] Processing Instagrapi...")
    instagrapi_b64 = ""
    try:
        cl = Client()
        settings = cl.get_settings()
        settings['cookies'] = cookie_dict
        if 'sessionid' in cookie_dict:
            settings['authorization_data'] = {'sessionid': cookie_dict['sessionid']}
        cl.set_settings(settings)
        
        # Save session file in the root
        ig_session_file = 'instagrapi_session.json'
        cl.dump_settings(ig_session_file)
        
        # Encode the file
        with open(ig_session_file, 'rb') as f:
            instagrapi_b64 = base64.b64encode(f.read()).decode('utf-8')
            
        print(f" [+] Instagrapi Session Encoded (saved to {ig_session_file})!")
        _write_env_var('INSTAGRAPI_SESSION_B64', instagrapi_b64)
    except Exception as e:
        print(f" [!] Instagrapi error: {e}")

    # ---------------------------------------------------------
    # 3. GENERATE INSTALOADER BASE64
    # ---------------------------------------------------------
    print("\n[2/2] Processing Instaloader...")
    instaloader_b64 = ""
    try:
        L = instaloader.Instaloader()
        
        # Inject the dictionary directly into Instaloader's internal session
        for name, value in cookie_dict.items():
            L.context._session.cookies.set(name, value, domain='.instagram.com')
            
        L.context.username = USERNAME
        
        # Save it to a local file in the root
        temp_file = f"session-{USERNAME}"
        L.save_session_to_file(temp_file)
        
        # Encode the file
        with open(temp_file, 'rb') as f:
            instaloader_b64 = base64.b64encode(f.read()).decode('utf-8')
            
        print(f" [+] Instaloader Session Encoded (saved to {temp_file})!")
        _write_env_var('INSTALOADER_SESSION_B64', instaloader_b64)
        
    except Exception as e:
        print(f" [!] Instaloader error: {e}")

    # ---------------------------------------------------------
    # FINAL OUTPUT
    # ---------------------------------------------------------
    print("\n" + "="*50)
    print(" [!] SUCCESS! SESSIONS WRITTEN TO YOUR .ENV FILE")
    print("="*50 + "\n")
    
    if instagrapi_b64:
        # Print first and last 20 characters so it's readable
        preview = f"{instagrapi_b64[:20]}...{instagrapi_b64[-20:]}"
        print(f"INSTAGRAPI_SESSION_B64  = {preview}")
        
    if instaloader_b64:
        preview = f"{instaloader_b64[:20]}...{instaloader_b64[-20:]}"
        print(f"INSTALOADER_SESSION_B64 = {preview}")

if __name__ == "__main__":
    generate_from_json()
