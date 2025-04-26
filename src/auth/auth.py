import os
import bcrypt
from src.auth.db import get_db_connection
from src import config
from groq import Groq

def register_user(userid, password, api_key):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        cursor.execute('INSERT INTO users (userid, password_hash, api_key) VALUES (?, ?, ?)',
                       (userid, password_hash, api_key))
        conn.commit()
        return True, "✅ Registered successfully!"
    except:
        return False, "❌ User already exists."
    finally:
        conn.close()

def login_user(userid, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash, api_key FROM users WHERE userid=?', (userid,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_hash, api_key = result
        if bcrypt.checkpw(password.encode(), stored_hash):
            return True, api_key
    return False, None


def verify_login(userid, password):
    # Verify the user's login credentials
    success, saved_api_key = login_user(userid, password)
    if success:
        config.api_key = saved_api_key
        os.environ["GROQ_API_KEY"] = saved_api_key
        return "✅ Login successful!" 
    else:
        return "❌ Incorrect userid or password."

def register_user_with_api_key(userid, password, user_api_key):
    # Validate the API Key first
    try:
        client = Groq(api_key=user_api_key)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama3-70b-8192"
        )

        # If API key is valid, proceed to register the user
        success, msg = register_user(userid, password, user_api_key)
        if success:
            config.api_key = user_api_key
            os.environ["GROQ_API_KEY"] = user_api_key
            return "✅ API Key validated & registered!"
        else:
            return msg

    except Exception as e:
        # API key invalid
        return f"❌ Invalid API Key: {str(e)}" 
    
    
def handle_login(userid, password, user_api_key):
    if user_api_key:
        # Handle registration with API key validation
        return register_user_with_api_key(userid, password, user_api_key)
    else:
        # Handle standard login
        return verify_login(userid, password)
