"""
auth.py — Authentication system for CortexDesk AI.

Provides signup, login, session management, and profile operations
backed by a SQLite database. Uses stdlib hashlib + secrets for
password hashing (no external dependencies).
"""

import sqlite3
import hashlib
import secrets
import re
import os
from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger(__name__)

DB_PATH = "data/users.db"


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------
def init_users_db():
    """Create the users table if it doesn't exist."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            security_question TEXT DEFAULT '',
            security_answer_hash TEXT DEFAULT '',
            total_tickets_analyzed INTEGER DEFAULT 0,
            total_escalations INTEGER DEFAULT 0,
            total_letters_generated INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)
    migrations = [
        ("security_question", "TEXT DEFAULT ''"),
        ("security_answer_hash", "TEXT DEFAULT ''"),
        ("total_tickets_analyzed", "INTEGER DEFAULT 0"),
        ("total_escalations", "INTEGER DEFAULT 0"),
        ("total_letters_generated", "INTEGER DEFAULT 0"),
    ]
    for col_name, col_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()
    logger.info("Users database initialized.")


# ---------------------------------------------------------------------------
# Password hashing — SHA-256 with per-user salt
# ---------------------------------------------------------------------------
def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """
    Hash a password with a random salt using SHA-256.
    Returns (hash_hex, salt_hex).
    """
    if salt is None:
        salt = secrets.token_hex(32)
    combined = f"{salt}{password}".encode("utf-8")
    hashed = hashlib.sha256(combined).hexdigest()
    return hashed, salt


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify a password against a stored hash + salt."""
    computed_hash, _ = _hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def _validate_username(username: str) -> str | None:
    """Returns error message or None if valid."""
    if not username or len(username.strip()) < 3:
        return "Username must be at least 3 characters."
    if len(username) > 30:
        return "Username must be 30 characters or fewer."
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return "Username can only contain letters, numbers, and underscores."
    return None


def _validate_email(email: str) -> str | None:
    """Returns error message or None if valid."""
    if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return "Please enter a valid email address."
    return None


def _validate_password(password: str) -> str | None:
    """Returns error message or None if valid."""
    if not password or len(password) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r'[a-zA-Z]', password):
        return "Password must contain at least one letter."
    if not re.search(r'[0-9]', password):
        return "Password must contain at least one digit."
    return None


# ---------------------------------------------------------------------------
# Public API — Signup
# ---------------------------------------------------------------------------
def signup(username: str, email: str, password: str,
           security_question: str = "", security_answer: str = "") -> dict:
    """
    Register a new user.

    Returns:
        {"success": True, "message": "..."} on success
        {"success": False, "message": "..."} on failure
    """
    # Validate inputs
    err = _validate_username(username)
    if err:
        return {"success": False, "message": err}

    err = _validate_email(email)
    if err:
        return {"success": False, "message": err}

    err = _validate_password(password)
    if err:
        return {"success": False, "message": err}

    username = username.strip().lower()
    email = email.strip().lower()

    # Hash password
    password_hash, salt = _hash_password(password)

    # Hash security answer if provided
    sec_answer_hash = ""
    if security_answer:
        sec_answer_hash, _ = _hash_password(security_answer.strip().lower(), salt)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, salt, created_at,
                               security_question, security_answer_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            username, email, password_hash, salt,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            security_question, sec_answer_hash
        ))
        conn.commit()
        logger.info(f"New user registered: {username}")
        return {"success": True, "message": "Account created successfully."}

    except sqlite3.IntegrityError as e:
        error_msg = str(e).lower()
        if "username" in error_msg:
            return {"success": False, "message": "Username already taken."}
        elif "email" in error_msg:
            return {"success": False, "message": "Email already registered."}
        return {"success": False, "message": "Account already exists."}

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Public API — Login
# ---------------------------------------------------------------------------
def login(username: str, password: str, remember_me: bool = False) -> dict:
    """
    Authenticate a user.

    Returns:
        {"success": True, "token": "...", "user": {...}} on success
        {"success": False, "message": "..."} on failure
    """
    if not username or not password:
        return {"success": False, "message": "Username and password are required."}

    username = username.strip().lower()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT password_hash, salt, email, created_at FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()

        if not row:
            return {"success": False, "message": "Invalid username or password."}

        stored_hash, salt, email, created_at = row

        if not _verify_password(password, stored_hash, salt):
            return {"success": False, "message": "Invalid username or password."}

        # Update last login
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE users SET last_login = ? WHERE username = ?", (now, username))

        # Generate session token
        token = secrets.token_hex(32)
        expires_dt = datetime.now() + (timedelta(days=30) if remember_me else timedelta(hours=8))
        expires = expires_dt.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO sessions (token, username, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, username, now, expires)
        )
        conn.commit()

        logger.info(f"User logged in: {username}")
        return {
            "success": True,
            "token": token,
            "user": {
                "username": username,
                "email": email,
                "created_at": created_at,
                "last_login": now,
            }
        }

    finally:
        conn.close()


def validate_session(token: str) -> dict | None:
    """Return the user payload for a valid session token, otherwise None."""
    if not token:
        return None

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT s.username, u.email, u.created_at, u.last_login, s.expires_at
            FROM sessions s
            JOIN users u ON u.username = s.username
            WHERE s.token = ?
        """, (token,))
        row = cursor.fetchone()
        if not row:
            return None

        username, email, created_at, last_login, expires_at = row
        try:
            expires = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            expires = datetime.min

        if expires <= datetime.now():
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None

        return {
            "username": username,
            "email": email,
            "created_at": created_at,
            "last_login": last_login,
        }
    finally:
        conn.close()


def logout_session(token: str):
    """Invalidate a single persisted session token."""
    if not token:
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Public API — Profile
# ---------------------------------------------------------------------------
def get_user(username: str) -> dict | None:
    """Retrieve user profile data. Returns None if user not found."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT username, email, created_at, last_login,
                   total_tickets_analyzed, total_escalations, total_letters_generated
            FROM users WHERE username = ?
        """, (username.strip().lower(),))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "username": row[0],
            "email": row[1],
            "created_at": row[2],
            "last_login": row[3],
            "total_tickets_analyzed": row[4] or 0,
            "total_escalations": row[5] or 0,
            "total_letters_generated": row[6] or 0,
        }
    finally:
        conn.close()


def increment_user_stat(username: str, field: str):
    """Increment a user statistic (total_tickets_analyzed, total_escalations, etc.)."""
    allowed = {"total_tickets_analyzed", "total_escalations", "total_letters_generated"}
    if field not in allowed:
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(f"UPDATE users SET {field} = {field} + 1 WHERE username = ?",
                     (username.strip().lower(),))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Public API — Password Reset
# ---------------------------------------------------------------------------
def verify_security_answer(username: str, answer: str) -> bool:
    """Verify a user's security answer for password reset."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT salt, security_answer_hash FROM users WHERE username = ?",
            (username.strip().lower(),)
        )
        row = cursor.fetchone()
        if not row or not row[1]:
            return False
        salt, stored_hash = row
        return _verify_password(answer.strip().lower(), stored_hash, salt)
    finally:
        conn.close()


def reset_password(username: str, new_password: str) -> dict:
    """Reset a user's password."""
    err = _validate_password(new_password)
    if err:
        return {"success": False, "message": err}

    username = username.strip().lower()
    password_hash, salt = _hash_password(new_password)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE username = ?",
            (password_hash, salt, username)
        )
        conn.commit()
        logger.info(f"Password reset for user: {username}")
        return {"success": True, "message": "Password reset successfully."}
    finally:
        conn.close()


def get_security_question(username: str) -> str | None:
    """Get a user's security question for password reset flow."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT security_question FROM users WHERE username = ?",
            (username.strip().lower(),)
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else None
    finally:
        conn.close()
