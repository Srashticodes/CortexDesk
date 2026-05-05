import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = "data/tickets.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create new schema v2
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ticket_text TEXT,
            domain TEXT,
            risk TEXT,
            decision TEXT,
            reason TEXT,
            domain_confidence REAL,
            risk_confidence REAL
        )
    ''')
    conn.commit()
    conn.close()

def log_ticket(ticket_text, domain, risk, decision, reason, domain_confidence, risk_confidence):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO tickets_v2 (timestamp, ticket_text, domain, risk, decision, reason, domain_confidence, risk_confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, ticket_text, domain, risk, decision, reason, domain_confidence, risk_confidence))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    # Check if tickets_v2 exists, otherwise return empty
    try:
        df = pd.read_sql_query("SELECT * FROM tickets_v2 ORDER BY timestamp DESC", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df
