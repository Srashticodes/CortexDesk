"""
cache_manager.py — Centralized caching for CortexDesk AI.

Provides LLM response caching and query deduplication to minimize
API token usage and improve response times on free-tier resources.
"""

import sqlite3
import hashlib
import json
import time
from datetime import datetime
from logger import get_logger

logger = get_logger(__name__)

DB_PATH = "data/cache.db"
DEFAULT_TTL = 3600  # 1 hour


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------
def init_cache_db():
    """Create the cache table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_cache (
            cache_key TEXT PRIMARY KEY,
            response TEXT NOT NULL,
            created_at REAL NOT NULL,
            ttl INTEGER NOT NULL,
            hit_count INTEGER DEFAULT 0,
            system_prompt_hash TEXT,
            token_estimate INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            hits INTEGER DEFAULT 0,
            misses INTEGER DEFAULT 0,
            total_calls INTEGER DEFAULT 0,
            tokens_saved INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


# Initialize on import
init_cache_db()


# ---------------------------------------------------------------------------
# Cache key generation
# ---------------------------------------------------------------------------
def _make_cache_key(system_prompt: str, user_prompt: str) -> str:
    """Generate a deterministic cache key from prompts."""
    combined = f"{system_prompt}|||{user_prompt}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def _estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token for English)."""
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Cache operations
# ---------------------------------------------------------------------------
def get_cached_response(system_prompt: str, user_prompt: str) -> str | None:
    """
    Look up a cached LLM response.

    Returns the cached response string if found and not expired,
    otherwise returns None.
    """
    key = _make_cache_key(system_prompt, user_prompt)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT response, created_at, ttl FROM llm_cache WHERE cache_key = ?",
            (key,)
        )
        row = cursor.fetchone()

        if not row:
            _record_miss(conn)
            return None

        response, created_at, ttl = row

        # Check expiry
        if time.time() - created_at > ttl:
            # Expired — delete and return None
            cursor.execute("DELETE FROM llm_cache WHERE cache_key = ?", (key,))
            conn.commit()
            _record_miss(conn)
            return None

        # Cache hit — increment counter
        cursor.execute(
            "UPDATE llm_cache SET hit_count = hit_count + 1 WHERE cache_key = ?",
            (key,)
        )
        conn.commit()
        _record_hit(conn, _estimate_tokens(response))

        logger.info(f"Cache HIT for key {key[:12]}...")
        return response

    finally:
        conn.close()


def cache_response(system_prompt: str, user_prompt: str, response: str,
                   ttl: int = DEFAULT_TTL):
    """Store an LLM response in the cache."""
    key = _make_cache_key(system_prompt, user_prompt)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            INSERT OR REPLACE INTO llm_cache
            (cache_key, response, created_at, ttl, system_prompt_hash, token_estimate)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            key, response, time.time(), ttl,
            hashlib.sha256(system_prompt.encode()).hexdigest()[:16],
            _estimate_tokens(response)
        ))
        conn.commit()
        logger.info(f"Cached response for key {key[:12]}...")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Stats tracking
# ---------------------------------------------------------------------------
def _get_today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _record_hit(conn: sqlite3.Connection, tokens_saved: int):
    """Record a cache hit in stats."""
    today = _get_today_key()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM cache_stats WHERE timestamp = ?", (today,))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE cache_stats SET hits = hits + 1, total_calls = total_calls + 1,
                   tokens_saved = tokens_saved + ? WHERE timestamp = ?
        """, (tokens_saved, today))
    else:
        cursor.execute("""
            INSERT INTO cache_stats (timestamp, hits, misses, total_calls, tokens_saved)
            VALUES (?, 1, 0, 1, ?)
        """, (today, tokens_saved))
    conn.commit()


def _record_miss(conn: sqlite3.Connection):
    """Record a cache miss in stats."""
    today = _get_today_key()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM cache_stats WHERE timestamp = ?", (today,))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE cache_stats SET misses = misses + 1, total_calls = total_calls + 1
            WHERE timestamp = ?
        """, (today,))
    else:
        cursor.execute("""
            INSERT INTO cache_stats (timestamp, hits, misses, total_calls, tokens_saved)
            VALUES (?, 0, 1, 1, 0)
        """, (today,))
    conn.commit()


def get_cache_stats() -> dict:
    """Get cache performance statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Today's stats
        today = _get_today_key()
        cursor.execute("SELECT hits, misses, total_calls, tokens_saved FROM cache_stats WHERE timestamp = ?", (today,))
        row = cursor.fetchone()
        today_stats = {
            "hits": row[0] if row else 0,
            "misses": row[1] if row else 0,
            "total_calls": row[2] if row else 0,
            "tokens_saved": row[3] if row else 0,
        }

        # Total cached entries
        cursor.execute("SELECT COUNT(*) FROM llm_cache")
        cached_entries = cursor.fetchone()[0]

        hit_rate = 0.0
        if today_stats["total_calls"] > 0:
            hit_rate = today_stats["hits"] / today_stats["total_calls"]

        return {
            "today": today_stats,
            "cached_entries": cached_entries,
            "hit_rate": round(hit_rate, 2),
        }
    finally:
        conn.close()


def clear_expired():
    """Remove expired cache entries."""
    conn = sqlite3.connect(DB_PATH)
    try:
        now = time.time()
        conn.execute("DELETE FROM llm_cache WHERE (? - created_at) > ttl", (now,))
        conn.commit()
    finally:
        conn.close()
