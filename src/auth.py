import sqlite3
from src.security.auth_manager import SecurityAuthManager

DB_NAME = "laundry_users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

def make_hashes(password: str) -> str:
    """Uses cryptographically salted PBKDF2-HMAC-SHA256."""
    return SecurityAuthManager.hash_password(password)

def check_hashes(password: str, hashed_text: str) -> bool:
    """Constant-time verification against timing attacks."""
    return SecurityAuthManager.verify_password(password, hashed_text)

def add_user(username: str, password: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', 
                  (username, make_hashes(password)))
        conn.commit()
        success = True
    except Exception:
        success = False
    conn.close()
    return success

def login_user(username: str, password: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    if row and check_hashes(password, row[0]):
        return [(username, row[0])]
    return []
