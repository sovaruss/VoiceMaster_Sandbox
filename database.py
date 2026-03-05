import sqlite3
from datetime import datetime

DB_NAME = "voice_master.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users 
                   (user_id INTEGER PRIMARY KEY, total_chars INTEGER DEFAULT 0, last_reset DATE)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS user_settings 
                   (user_id INTEGER PRIMARY KEY, pause_ratio INTEGER DEFAULT 100)''')
    conn.commit()
    conn.close()

def check_limit(user_id, chars, daily_limit, admin_id):
    if user_id == admin_id: return True
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    today = datetime.now().date()
    cur.execute('SELECT total_chars, last_reset FROM users WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    
    if not res:
        cur.execute('INSERT INTO users VALUES (?, ?, ?)', (user_id, chars, today))
        conn.commit()
        return chars <= daily_limit
    
    total, last_date = res
    if str(last_date) != str(today):
        total = chars
    else:
        total += chars
        
    if total > daily_limit: return False
    cur.execute('UPDATE users SET total_chars = ?, last_reset = ? WHERE user_id = ?', (total, today, user_id))
    conn.commit()
    return True

def get_pause(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT pause_ratio FROM user_settings WHERE user_id = ?", (user_id,))
    res = cur.fetchone()
    return res[0] if res else 100

def set_pause(user_id, val):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO user_settings VALUES (?, ?)", (user_id, val))
    conn.commit()
    conn.close()