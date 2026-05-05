import os
import json
import requests

# ---------------------------------------------------------------------------
# Provider configuration — change LLM_PROVIDER to switch between Groq and
# Anthropic. Everything else (classifier, risk_engine, responder) stays the
# same — they all import call_llm() from here.
# ---------------------------------------------------------------------------

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")   # "groq" | "anthropic"

# Groq settings
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"   # best free-tier model on Groq

# Anthropic settings
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL   = "claude-haiku-4-5-20251001"


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str | None:
    """
    Send a system + user prompt to the configured LLM provider.
    Returns the response text string, or None if the call fails.

    Usage:
        from llm_client import call_llm
        result = call_llm(system_prompt="You are...", user_prompt="Ticket: ...")
    """
    if LLM_PROVIDER == "groq":
        return _call_groq(system_prompt, user_prompt, max_tokens)
    elif LLM_PROVIDER == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, max_tokens)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{LLM_PROVIDER}'. Use 'groq' or 'anthropic'.")


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