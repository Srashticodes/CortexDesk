import json
from llm_client import call_llm

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_TOKENS        = 512
MAX_DOC_CHARS     = 3000   # cap total RAG context sent to LLM


# ---------------------------------------------------------------------------
# System prompt — tells the LLM exactly what role it plays
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a professional customer support agent. Your job is to write a clear, empathetic, and helpful reply to a customer support ticket.

You will be given:
- The customer's original ticket
- The detected service domain (e.g. Visa, Amazon, Apple)
- The risk level (high / medium / low)
- The decision (escalate / respond_and_escalate / respond)
- Relevant knowledge-base snippets to draw from

Rules:
- Write in a warm, professional tone. Never robotic or templated-sounding.
- Use the knowledge-base snippets as your factual source. Do not invent facts.
- If the decision is "escalate", focus on reassurance and next steps — tell the customer their case is being prioritised.
- If the decision is "respond_and_escalate", answer what you can and mention that a specialist will follow up.
- If the decision is "respond", give a complete, self-contained answer based on the snippets.
- Keep the response concise — 3 to 6 sentences for low-risk tickets, slightly longer for high-risk.
- Do NOT include subject lines, JSON, or any formatting markers. Just the reply text.
- Do NOT start with "I" — begin with the customer in mind (e.g. "Thank you for reaching out..." or "We're sorry to hear...").
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _build_user_prompt(
    ticket: str,
    domains: list[str],
    risk: str,
    decision: str,
    category: str,
    triggers: list[str],
    docs: list[str],
) -> str:
    """Assembles the user-turn message sent to the LLM."""

    # Truncate docs to avoid blowing the context window
    combined_docs = "\n".join(f"- {d.strip()}" for d in docs if d.strip())
    if len(combined_docs) > MAX_DOC_CHARS:
        combined_docs = combined_docs[:MAX_DOC_CHARS] + "\n[...additional docs truncated]"

    docs_section = combined_docs if combined_docs else "No knowledge-base snippets available."

    triggers_text = ", ".join(triggers) if triggers else "none"
    domains_text  = ", ".join(domains)  if domains  else "Unknown"

    return f"""TICKET:
\"\"\"{ticket}\"\"\"

CONTEXT:
- Domain(s): {domains_text}
- Risk level: {risk}
- Risk category: {category}
- Decision: {decision}
- Detected triggers: {triggers_text}

KNOWLEDGE BASE SNIPPETS:
{docs_section}

Write the customer reply now."""


def _call_llm(user_prompt: str) -> str | None:
    """
    Calls the configured LLM provider (Groq or Anthropic).
    Returns the response text, or None if the call fails.
    """
    return call_llm(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt, max_tokens=MAX_TOKENS)


# ---------------------------------------------------------------------------
# Fallback — used when no ANTHROPIC_API_KEY is set or the LLM call fails
# ---------------------------------------------------------------------------
def _fallback_response(
    docs: list[str],
    decision: str,
    category: str,
    domains: list[str],
    triggers: list[str],
) -> str:
    """
    Template-based response. Identical logic to the original responder.py so
    the app keeps working out of the box even without an API key.
    """
    # Tone
    if category == "SECURITY_COMPROMISE":
        greeting    = "🚨 URGENT: We detected a potential security issue."
        instruction = "Please take the following steps immediately:"
        closing     = "Your safety is our top priority. Contact support immediately if needed."
    elif category == "BILLING_ISSUE":
        greeting    = "Hello, we understand billing issues can be frustrating."
        instruction = "Here's what we found regarding your payment issue:"
        closing     = "If the issue persists, please contact support for further assistance."
    else:
        greeting    = "Hello,"
        instruction = "Based on our documentation, here are some steps that may help:"
        closing     = "If you still need assistance, please let us know."

    # Security escalation override
    if decision == "escalate" and category == "SECURITY_COMPROMISE":
        return (
            f"{greeting}\n\n"
            "We strongly recommend taking immediate action:\n"
            "• Change your account password\n"
            "• Enable two-factor authentication\n"
            "• Review recent account activity\n"
            "• Contact official support immediately\n\n"
            "This issue has been escalated to our high-priority security team.\n"
        )

    # Generic escalation
    if decision == "escalate":
        return (
            f"{greeting}\n\n"
            "This issue requires special attention. "
            "Our support team will contact you shortly.\n\n"
            f"{closing}\n"
        )

    # Escalation note
    escalation_note = "\n\n⚠️ We have also escalated this issue for further review." \
        if decision == "respond_and_escalate" else ""

    # Trigger hints
    trigger_hint = ""
    if triggers:
        if any("charged twice" in t or "duplicate" in t for t in triggers):
            trigger_hint = "\n\nIt appears you may have experienced a duplicate or temporary authorization charge."
        elif any("unknown purchase" in t or "unauthorized" in t for t in triggers):
            trigger_hint = "\n\nWe detected signs of potentially unauthorized activity."

    # Multi-domain note
    domain_context = ""
    if domains and len(domains) > 1:
        domain_context = f"\n\nThis issue appears to involve multiple services: {', '.join(domains)}."

    # Docs
    formatted_docs = (
        "\n".join(f"- {d.strip()}" for d in docs if d.strip())
        or "Our team will review your request and respond shortly."
    )

    return (
        f"{greeting}\n\n"
        f"{instruction}"
        f"{trigger_hint}\n\n"
        f"{formatted_docs}\n\n"
        f"{closing}{escalation_note}{domain_context}\n"
    )


# ---------------------------------------------------------------------------
# Public API — same signature as the original, fully backwards compatible
# ---------------------------------------------------------------------------
def generate_response(
    docs: list[str],
    decision: str,
    category: str,
    domains: list[str] | None = None,
    triggers: list[str] | None = None,
    ticket: str = "",           # NEW optional param — pass the original ticket text
) -> str:
    """
    Generate a customer-facing reply.

    Tries the LLM path first (requires ANTHROPIC_API_KEY in env).
    Falls back to the original template-based approach if the key is missing
    or the API call fails — so the app always works.

    Args:
        docs:      Retrieved knowledge-base snippets.
        decision:  "escalate" | "respond_and_escalate" | "respond"
        category:  Risk category string from risk_engine (e.g. "SECURITY_COMPROMISE")
        domains:   List of matched domain names (primary first).
        triggers:  List of risk trigger strings detected in the ticket.
        ticket:    The original customer ticket text (used by LLM for context).

    Returns:
        A plain-text customer reply string.
    """
    domains  = domains  or []
    triggers = triggers or []

    # --- Try the LLM path ---
    if ticket:
        user_prompt = _build_user_prompt(
            ticket=ticket,
            domains=domains,
            risk=_risk_from_decision(decision),
            decision=decision,
            category=category,
            triggers=triggers,
            docs=docs,
        )
        llm_response = _call_llm(user_prompt)
        if llm_response:
            return llm_response

    # --- Fallback to templates ---
    return _fallback_response(
        docs=docs,
        decision=decision,
        category=category,
        domains=domains,
        triggers=triggers,
    )


def _risk_from_decision(decision: str) -> str:
    """Infer a human-readable risk level from the decision string."""
    if decision == "escalate":
        return "high"
    if decision == "respond_and_escalate":
        return "medium"
    return "low"