import sqlite3
from datetime import datetime, timedelta

DB_NAME = "voice_master.db"

def get_stats(user_id=None, is_admin_query=False):
    """
    Универсальная функция для получения статистики.
    Если передан user_id — считает для него.
    is_admin_query — если True, считает для всех (для команды /usage).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Базовый запрос
    query = "SELECT SUM(chars_count) FROM usage_log WHERE"
    params = []
    
    if user_id is not None:
        query += " user_id = ?"
        params.append(user_id)
    else:
        query += " 1=1" # Просто заглушка для корректного WHERE
        
    periods = {
        "today": "date(timestamp) = date('now')",
        "week": "date(timestamp) >= date('now', '-7 days')",
        "month": "date(timestamp) >= date('now', '-30 days')",
        "year": "date(timestamp) >= date('now', '-365 days')"
    }
    
    results = {}
    for period, condition in periods.items():
        full_query = f"{query} AND {condition}"
        cursor.execute(full_query, params)
        val = cursor.fetchone()[0]
        results[period] = val if val else 0
        
    conn.close()
    return results

def get_system_metrics():
    """Статистика использования голосов и времени (для /metrics)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Популярность голосов
    cursor.execute("SELECT voice_used, COUNT(*) FROM usage_log GROUP BY voice_used")
    voices = cursor.fetchall()
    
    # Общее кол-во юзеров
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Новые сегодня
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_reset = date('now')")
    new_today = cursor.fetchone()[0]
    
    conn.close()
    return {
        "voices": voices,
        "total_users": total_users,
        "new_today": new_today
    }