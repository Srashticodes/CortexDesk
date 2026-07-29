import json
import re
from llm_client import call_llm

# ---------------------------------------------------------------------------
# analyzer.py — combines classify + risk into ONE Groq call
#
# Before: triage.py called classify_ticket() → Groq call 1
#                    then analyze_risk()      → Groq call 2
#         Total: 2 sequential HTTP round trips before even reaching responder
#
# After:  triage.py calls analyze_ticket()   → 1 Groq call returns both
#         Total: 1 HTTP round trip, ~50% latency reduction
#
# Falls back gracefully: if the LLM call fails, it delegates to the
# original classify_ticket() and analyze_risk() functions individually.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a customer support ticket analyzer. Given a ticket, return BOTH the domain classification AND the risk assessment in a single JSON response.

Available domains: {domains}

Risk levels:
- high: Security breach, fraud, unauthorized access, account compromise, significant financial loss
- medium: Billing disputes, suspected unauthorized charges, account access issues, significant technical failures  
- low: Standard support queries, minor bugs, general questions, routine refund requests

Risk categories: SECURITY_COMPROMISE, BILLING_ISSUE, TECH_ISSUE, GENERAL

Return ONLY this JSON object — no markdown, no explanation:
{{
  "domain": {{
    "primary": "<domain name>",
    "secondary": ["<domain>"],
    "confidence": <0.0-1.0>
  }},
  "risk": {{
    "level": "high" | "medium" | "low",
    "confidence": <0.0-1.0>,
    "category": "SECURITY_COMPROMISE" | "BILLING_ISSUE" | "TECH_ISSUE" | "GENERAL",
    "triggers": ["<phrase that drove the assessment>"],
    "reason": "<one sentence>"
  }}
}}"""


def _heuristic_analysis(ticket_text: str, services: dict) -> dict | None:
    """Fast, keyword-based analysis that avoids the LLM for obvious tickets."""
    lowered = ticket_text.lower()
    scores: dict[str, int] = {}

    for name, service in services.items():
        score = 0
        for keyword in service.get("keywords", []):
            keyword_lower = keyword.lower()
            if keyword_lower in lowered:
                score += 3 if " " in keyword_lower else 2
        for risk_word in service.get("risk_words", []):
            if risk_word.lower() in lowered:
                score += 2
        if name.lower() in lowered:
            score += 4
        scores[name] = score

    if not scores:
        return None

    primary, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score <= 0:
        return None

    secondary = [
        name for name, score in scores.items()
        if name != primary and score > 0 and score >= best_score * 0.6
    ]
    confidence = min(0.55 + (best_score * 0.08), 0.95)
    if confidence < 0.72:
        return None

    risk_level = "low"
    category = "GENERAL"
    triggers: list[str] = []
    security_terms = ["hacked", "stolen", "unauthorized", "fraud", "compromised", "scam", "phishing"]
    billing_terms = ["charged twice", "duplicate charge", "refund", "billing", "overcharged", "cancel subscription", "money deducted"]
    tech_terms = ["error", "bug", "not working", "timeout", "crash", "broken", "bricked"]

    if any(term in lowered for term in security_terms):
        risk_level = "high"
        category = "SECURITY_COMPROMISE"
        triggers = [term for term in security_terms if term in lowered][:3]
    elif any(term in lowered for term in billing_terms):
        risk_level = "medium"
        category = "BILLING_ISSUE"
        triggers = [term for term in billing_terms if term in lowered][:3]
    elif any(term in lowered for term in tech_terms):
        risk_level = "medium"
        category = "TECH_ISSUE"
        triggers = [term for term in tech_terms if term in lowered][:3]

    return {
        "domain": {
            "primary": primary,
            "secondary": secondary,
            "confidence": round(confidence, 2),
            "source": "heuristic",
        },
        "risk": {
            "level": risk_level,
            "confidence": round(min(0.8, confidence), 2),
            "category": category,
            "triggers": triggers,
            "reason": "Keyword-based analysis matched a clear support pattern.",
            "score": {"high": 100, "medium": 50, "low": 10}[risk_level],
            "source": "heuristic",
        },
    }


def analyze_ticket(ticket_text: str, services: dict) -> dict | None:
    """
    Single LLM call that returns both domain classification and risk assessment.

    Returns a dict with 'domain' and 'risk' keys, or None if the call fails.
    On failure, triage.py falls back to calling classify_ticket() and
    analyze_risk() individually.

    Return shape:
    {
        "domain": {
            "primary":    str,
            "secondary":  list[str],
            "confidence": float,
        },
        "risk": {
            "level":      str,
            "confidence": float,
            "category":   str,
            "triggers":   list[str],
            "reason":     str,
        }
    }
    """
    heuristic = _heuristic_analysis(ticket_text, services)
    if heuristic is not None:
        return heuristic

    domain_names = list(services.keys())
    domains_str  = ", ".join(domain_names)

    system = SYSTEM_PROMPT.format(domains=domains_str)
    user   = f"Ticket:\n{ticket_text}"

    try:
        raw = call_llm(system_prompt=system, user_prompt=user, max_tokens=400)
        if not raw:
            return None

        # Strip accidental markdown fences
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)

        # --- Validate domain block ---
        domain_block = data.get("domain", {})
        primary = domain_block.get("primary", "")
        if primary not in domain_names:
            primary = domain_names[0]  # safe fallback

        secondary = [
            d for d in domain_block.get("secondary", [])
            if d in domain_names and d != primary
        ]
        domain_confidence = float(domain_block.get("confidence", 0.75))

        # --- Validate risk block ---
        risk_block = data.get("risk", {})
        level = risk_block.get("level", "low")
        if level not in ("high", "medium", "low"):
            level = "low"

        category = risk_block.get("category", "GENERAL")
        if category not in ("SECURITY_COMPROMISE", "BILLING_ISSUE", "TECH_ISSUE", "GENERAL"):
            category = "GENERAL"

        return {
            "domain": {
                "primary":    primary,
                "secondary":  secondary,
                "confidence": round(domain_confidence, 2),
                "source":     "llm",
            },
            "risk": {
                "level":      level,
                "confidence": round(float(risk_block.get("confidence", 0.80)), 2),
                "category":   category,
                "triggers":   risk_block.get("triggers", []),
                "reason":     risk_block.get("reason", ""),
                "score":      {"high": 100, "medium": 50, "low": 10}[level],
                "source":     "llm",
            }
        }

    except Exception:
        return None  # caller falls back to individual functions