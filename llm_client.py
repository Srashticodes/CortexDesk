import os
import json
import requests
from cache_manager import get_cached_response, cache_response

# ---------------------------------------------------------------------------
# Provider configuration — change LLM_PROVIDER to switch between Groq,
# Anthropic, or OpenAI. Everything else (classifier, risk_engine, responder)
# stays the same — they all import call_llm() from here.
# ---------------------------------------------------------------------------

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")   # "groq" | "anthropic" | "openai"

# Groq settings
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"   # best free-tier model on Groq

# Anthropic settings
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL   = "claude-haiku-4-5-20251001"

# OpenAI settings
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL   = os.environ.get("OPENAI_MODEL", "gpt-4.1")

# ---------------------------------------------------------------------------
# Call metrics — tracked in memory for the current session
# ---------------------------------------------------------------------------
_call_stats = {"total": 0, "cached": 0, "api": 0, "failed": 0}


def get_call_stats() -> dict:
    """Return LLM call statistics for the current session."""
    return _call_stats.copy()


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 512,
             use_cache: bool = True) -> str | None:
    """
    Send a system + user prompt to the configured LLM provider.
    Returns the response text string, or None if the call fails.

    Checks cache before making API calls to reduce token usage.

    Usage:
        from llm_client import call_llm
        result = call_llm(system_prompt="You are...", user_prompt="Ticket: ...")
    """
    _call_stats["total"] += 1

    # Check cache first
    if use_cache:
        cached = get_cached_response(system_prompt, user_prompt)
        if cached is not None:
            _call_stats["cached"] += 1
            return cached

    # Make API call
    result = None
    if LLM_PROVIDER == "groq":
        result = _call_groq(system_prompt, user_prompt, max_tokens)
    elif LLM_PROVIDER == "anthropic":
        result = _call_anthropic(system_prompt, user_prompt, max_tokens)
    elif LLM_PROVIDER == "openai":
        result = _call_openai(system_prompt, user_prompt, max_tokens)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{LLM_PROVIDER}'. Use 'groq', 'anthropic', or 'openai'.")

    # Cache the result if successful
    if result is not None:
        _call_stats["api"] += 1
        if use_cache:
            cache_response(system_prompt, user_prompt, result)
    else:
        _call_stats["failed"] += 1

    return result


# ---------------------------------------------------------------------------
# Groq — OpenAI-compatible format
# ---------------------------------------------------------------------------
def _call_groq(system_prompt: str, user_prompt: str, max_tokens: int) -> str | None:
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return None

    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    except Exception:
        return None


# ---------------------------------------------------------------------------
# Anthropic — native messages format
# ---------------------------------------------------------------------------
def _call_anthropic(system_prompt: str, user_prompt: str, max_tokens: int) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    try:
        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()

    except Exception:
        return None


# ---------------------------------------------------------------------------
# OpenAI — chat completions
# ---------------------------------------------------------------------------
def _call_openai(system_prompt: str, user_prompt: str, max_tokens: int) -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None

    try:
        resp = requests.post(
            OPENAI_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    except Exception:
        return None