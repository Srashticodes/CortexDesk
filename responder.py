import json
import re
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
- Paraphrase the knowledge-base snippets instead of repeating them word-for-word. Use them as the factual source, then rewrite naturally.
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def compress_docs(docs: list[str], max_docs: int = 3, max_chars: int = 2200) -> list[str]:
    """Trim and de-duplicate retrieved docs before sending them to the LLM."""
    cleaned: list[str] = []
    seen: set[str] = set()

    for doc in docs or []:
        text = " ".join(str(doc).strip().split())
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)

    if not cleaned:
        return []

    compressed: list[str] = []
    current_chars = 0
    for text in cleaned[:max_docs]:
        if current_chars + len(text) + 1 > max_chars and compressed:
            break
        compressed.append(text)
        current_chars += len(text) + 1

    return compressed


def _should_use_template(ticket: str, decision: str, category: str, triggers: list[str]) -> bool:
    """Use a concise template for common issues to avoid an unnecessary LLM call."""
    if decision != "respond":
        return False

    lowered = (ticket or "").lower()
    common_terms = [
        "refund", "charged twice", "duplicate charge", "billing",
        "password", "login", "reset", "account recovery", "cancel subscription",
        "continue watching", "watching list", "watchlist", "stream", "playback", "error while streaming",
    ]
    if any(term in lowered for term in common_terms):
        return True
    return category == "BILLING_ISSUE" and any("charge" in t.lower() or "refund" in t.lower() for t in triggers)


def _template_response(ticket: str) -> str:
    """Compact, support-style response for common low-risk issues."""
    lowered = (ticket or "").lower()

    if any(term in lowered for term in ["continue watching", "watching list", "watchlist", "stream", "playback", "error while streaming"]):
        return (
            "Thanks for letting us know. It looks like your continue watching list may need a refresh, so please restart the Netflix app and make sure you are on the correct profile. "
            "If the list still does not update, sign out and sign back in to refresh your progress."
        )
    if any(term in lowered for term in ["refund", "charged twice", "duplicate charge", "billing"]):
        return (
            "Thank you for flagging this. We have identified a billing concern that should be reviewed carefully. "
            "Please keep your order or transaction details handy, and our support team will follow up with the appropriate next steps."
        )
    if any(term in lowered for term in ["password", "login", "reset", "account recovery"]):
        return (
            "Thanks for reaching out. Please try the standard account recovery steps first, and verify the details you entered. "
            "If the issue continues, our support team will guide you through the next steps."
        )
    return (
        "Thanks for reaching out. We have noted your request and will review it with the relevant support guidance. "
        "If more details are needed, our team will follow up promptly."
    )


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

    compact_docs = compress_docs(docs, max_docs=3, max_chars=MAX_DOC_CHARS)

    # Truncate docs to avoid blowing the context window
    combined_docs = "\n".join(f"- {d.strip()}" for d in compact_docs if d.strip())
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

Write the customer reply now.
Use a warm, natural tone and do not quote the snippets verbatim.
Summarize the relevant facts in your own words.
Avoid document-style language and keep the reply friendly and natural."""


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
    ticket: str = "",
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

    docs_summary = _summarize_docs_for_reply(docs, ticket)
    support_summary = (
        f"\n\nAccording to the relevant knowledge base, {docs_summary}"
        if docs_summary else "\n\nOur team will review your request and respond shortly."
    )

    return (
        f"{greeting}\n\n"
        f"{instruction}"
        f"{trigger_hint}"
        f"{support_summary}\n\n"
        f"{closing}{escalation_note}{domain_context}\n"
    )


def _summarize_docs_for_reply(docs: list[str], ticket: str = "") -> str:
    """Create a short, user-facing summary from retrieved knowledge base snippets and the ticket."""
    ticket_text = (ticket or "").lower()
    doc_text = " ".join(str(doc).strip().lower() for doc in docs if str(doc).strip())

    if any(term in ticket_text for term in ["continue watching", "watching list", "watchlist", "profile", "playback", "stream", "streaming error"]):
        return "refreshing the app and making sure you are on the right profile often helps resolve continue watching list issues."
    if any(term in ticket_text for term in ["password", "login", "reset", "account recovery"]):
        return "account recovery steps and login verification are the best next steps for this issue."
    if any(term in ticket_text for term in ["refund", "charged twice", "duplicate charge", "billing"]):
        return "we recommend reviewing the payment or refund details and confirming the transaction information."
    if any(term in ticket_text for term in ["unauthorized", "fraud", "compromised", "unknown purchase"]):
        return "securing the account and reviewing any unfamiliar activity is the prioritized action."

    if any(term in doc_text for term in ["continue watching", "watching list", "watchlist", "profile", "playback", "stream", "streaming"]):
        return "refreshing the app, checking your connection, and confirming the correct profile are good first steps."
    if any(term in doc_text for term in ["refund", "charge", "billing", "duplicate charge", "authorization"]):
        return "we recommend reviewing the payment or refund details and confirming the transaction information."
    if any(term in doc_text for term in ["password", "login", "reset", "account recovery"]):
        return "account recovery steps and login verification are the best next steps for this issue."
    if any(term in doc_text for term in ["unauthorized", "fraud", "suspicious", "unknown purchase"]):
        return "securing the account and reviewing any unfamiliar activity is the prioritized action."

    return "we found relevant support guidance for this issue and will make sure the team follows it."

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

    compact_docs = compress_docs(docs, max_docs=3, max_chars=MAX_DOC_CHARS)

    if ticket and _should_use_template(ticket, decision, category, triggers):
        return _template_response(ticket)

    # --- Try the LLM path ---
    if ticket:
        user_prompt = _build_user_prompt(
            ticket=ticket,
            domains=domains,
            risk=_risk_from_decision(decision),
            decision=decision,
            category=category,
            triggers=triggers,
            docs=compact_docs,
        )
        llm_response = _call_llm(user_prompt)
        if llm_response:
            return llm_response

    # --- Fallback to templates ---
    return _fallback_response(
        docs=compact_docs,
        decision=decision,
        category=category,
        domains=domains,
        triggers=triggers,
        ticket=ticket,
    )


def _risk_from_decision(decision: str) -> str:
    """Infer a human-readable risk level from the decision string."""
    if decision == "escalate":
        return "high"
    if decision == "respond_and_escalate":
        return "medium"
    return "low"