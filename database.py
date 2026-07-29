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

    # ---------------------------------------------------------------------------
    # Schema migration — add columns for explainability and letter generation
    # Uses ALTER TABLE with try/except so it's safe to run repeatedly.
    # ---------------------------------------------------------------------------
    migrations = [
        ("response", "TEXT DEFAULT ''"),
        ("category", "TEXT DEFAULT ''"),
        ("triggers", "TEXT DEFAULT ''"),
        ("analysis_source", "TEXT DEFAULT ''"),
        ("retrieval_scores", "TEXT DEFAULT ''"),
    ]
    for col_name, col_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE tickets_v2 ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Escalation letters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escalation_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            timestamp TEXT,
            subject TEXT,
            body TEXT,
            severity TEXT,
            domain TEXT,
            generated_by TEXT DEFAULT '',
            FOREIGN KEY (ticket_id) REFERENCES tickets_v2(id)
        )
    ''')

    conn.commit()
    conn.close()

def log_ticket(ticket_text, domain, risk, decision, reason, domain_confidence, risk_confidence,
               response="", category="", triggers="", analysis_source="", retrieval_scores=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Serialize triggers list to comma-separated string
    if isinstance(triggers, list):
        triggers = ", ".join(triggers)

    cursor.execute('''
        INSERT INTO tickets_v2 (timestamp, ticket_text, domain, risk, decision, reason,
                                domain_confidence, risk_confidence, response, category,
                                triggers, analysis_source, retrieval_scores)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, ticket_text, domain, risk, decision, reason,
          domain_confidence, risk_confidence, response, category,
          triggers, analysis_source, retrieval_scores))

    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

def get_history():
    conn = sqlite3.connect(DB_PATH)
    # Check if tickets_v2 exists, otherwise return empty
    try:
        df = pd.read_sql_query("SELECT * FROM tickets_v2 ORDER BY timestamp DESC", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def get_ticket_by_id(ticket_id: int) -> dict | None:
    """Retrieve a single ticket by its database ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM tickets_v2 WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    finally:
        conn.close()

def save_escalation_letter(ticket_id: int, subject: str, body: str,
                           severity: str, domain: str, generated_by: str = ""):
    """Save a generated escalation letter to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO escalation_letters (ticket_id, timestamp, subject, body, severity, domain, generated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ticket_id, timestamp, subject, body, severity, domain, generated_by))
    conn.commit()
    conn.close()

def get_user_letters(generated_by: str = "") -> pd.DataFrame:
    """Get all escalation letters, optionally filtered by user."""
    conn = sqlite3.connect(DB_PATH)
    try:
        if generated_by:
            df = pd.read_sql_query(
                "SELECT * FROM escalation_letters WHERE generated_by = ? ORDER BY timestamp DESC",
                conn, params=(generated_by,)
            )
        else:
            df = pd.read_sql_query(
                "SELECT * FROM escalation_letters ORDER BY timestamp DESC", conn
            )
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df
