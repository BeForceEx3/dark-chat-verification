import sqlite3, hashlib, random
from datetime import datetime, timedelta

class EmailVerification:
    def __init__(self, db_path='codes.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute('''CREATE TABLE IF NOT EXISTS codes (
            email_hash TEXT PRIMARY KEY,
            code TEXT NOT NULL,
            is_valid INTEGER DEFAULT 1,
            attempts INTEGER DEFAULT 0,
            expires_at TEXT
        )''')
        conn.commit()
        conn.close()
    
    # generate_code, hash_email, send_code, verify_code...
