import sqlite3
from src.config import DB_PATH

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            userid TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            api_key TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
