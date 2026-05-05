import re
import json
from llm_client import call_llm

# ---------------------------------------------------------------------------
# Regex pre-filter — lightweight first pass to catch obvious signals fast.
# These are NOT used for final scoring anymore. They serve two purposes:
#   1. Quick "is this worth sending to the LLM?" check
#   2. Populating the `triggers` list returned in the result
# ---------------------------------------------------------------------------
SIGNAL_PATTERNS = {
    "SECURITY_COMPROMISE": [
        r"\b(hacked|stolen|unauthorized|compromised)\b",
        r"\b(accessed without (my )?permission)\b",
        r"\b(someone (else )?logged into)\b",
        r"\b(unknown purchase[s]?|charge I didn't make|fraudulent)\b",
        r"\b(brute force|bypass(ed)? security)\b",
        r"\b(scam|phishing)\b",
    ],
    "BILLING_ISSUE": [
        r"\b(double charged|charged twice|duplicate charge)\b",
        r"\b(overcharged|wrong amount)\b",
        r"\b(refund|cancel(led)? subscription)\b",
        r"\b(dispute|chargeback)\b",
        r"\b(money deducted)\b",
    ],
    "TECH_ISSUE": [
        r"\b(broken|error|crash(ed)?|not working|timeout)\b",
        r"\b(bug|glitch|fail(ed)?)\b",
        r"\b(bricked|won'?t turn on)\b",
    ],
}

# ---------------------------------------------------------------------------
# LLM prompt — asks Claude to assess risk with full semantic understanding
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a support ticket risk assessor. Given a customer support ticket, assess its risk level.

Risk levels:
- high: Security breach, fraud, unauthorized access, account compromise, significant financial loss
- medium: Billing disputes, suspected unauthorized charges, account access issues, significant technical failures
- low: Standard support queries, minor bugs, general questions, routine refund requests

Return ONLY a JSON object — no markdown, no explanation:
{
  "level": "high" | "medium" | "low",
  "confidence": <0.0 to 1.0>,
  "category": "SECURITY_COMPROMISE" | "BILLING_ISSUE" | "TECH_ISSUE" | "GENERAL",
  "reason": "<one sentence explaining the risk level>",
  "triggers": ["<specific phrase that drove the assessment>", ...]
}"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _regex_scan(text: str) -> tuple[list[str], str]:
    """
    Run the lightweight regex pass.
    Returns (detected_trigger_strings, dominant_category).
    """
    lowered = text.lower()
    triggers: list[str] = []
    category_hits: dict[str, int] = {}

    for category, patterns in SIGNAL_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, lowered):
                phrase = match.group(0)
                if phrase not in triggers:
                    triggers.append(phrase)
                    category_hits[category] = category_hits.get(category, 0) + 1

    dominant = max(category_hits, key=category_hits.get) if category_hits else "GENERAL"
    return triggers, dominant


def _call_llm(ticket_text: str) -> dict | None:
    """
    Ask the configured LLM to assess risk level with semantic understanding.
    Returns the parsed result dict or None on failure.
    """
    try:
        raw = call_llm(system_prompt=SYSTEM_PROMPT, user_prompt=f"Ticket:\n{ticket_text}", max_tokens=256)
        if not raw:
            return None
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)

        # Validate required fields
        if data.get("level") not in ("high", "medium", "low"):
            return None
        if data.get("category") not in ("SECURITY_COMPROMISE", "BILLING_ISSUE", "TECH_ISSUE", "GENERAL"):
            data["category"] = "GENERAL"

        return {
            "level":      data["level"],
            "score":      {"high": 100, "medium": 50, "low": 10}[data["level"]],  # synthetic score for UI
            "confidence": round(float(data.get("confidence", 0.85)), 2),
            "triggers":   data.get("triggers", []),
            "category":   data["category"],
            "source":     "llm",
        }

    except Exception:
        return None


def _fallback_score(text: str, triggers: list[str], dominant_category: str) -> dict:
    """
    Original weighted regex scoring — used when LLM is unavailable.
    Kept as-is so the app always works without an API key.
    """
    WEIGHTS = {
        "SECURITY_COMPROMISE": [
            (r"\b(hacked|stolen|unauthorized|compromised)\b",        80),
            (r"\b(accessed without (my )?permission)\b",             90),
            (r"\b(someone (else )?logged into)\b",                   90),
            (r"\b(unknown purchase[s]?|charge I didn't make|fraudulent)\b", 85),
            (r"\b(brute force|bypass(ed)? security)\b",              80),
            (r"\b(scam|phishing)\b",                                 60),
        ],
        "BILLING_ISSUE": [
            (r"\b(double charged|charged twice|duplicate charge)\b", 50),
            (r"\b(overcharged|wrong amount)\b",                      40),
            (r"\b(refund|cancel(led)? subscription)\b",              20),
            (r"\b(dispute|chargeback)\b",                            50),
            (r"\b(money deducted)\b",                                40),
        ],
        "TECH_ISSUE": [
            (r"\b(broken|error|crash(ed)?|not working|timeout)\b",   20),
            (r"\b(bug|glitch|fail(ed)?)\b",                          20),
            (r"\b(bricked|won'?t turn on)\b",                        40),
        ],
    }

    lowered = text.lower()
    total_score = 0
    max_cat_score = 0
    primary_category = "GENERAL"

    for category, patterns in WEIGHTS.items():
        cat_score = 0
        for pattern, weight in patterns:
            for match in re.finditer(pattern, lowered):
                phrase = match.group(0)
                if phrase not in triggers:
                    triggers.append(phrase)
                cat_score += weight
        total_score += cat_score
        if cat_score > max_cat_score:
            max_cat_score = cat_score
            primary_category = category

    if total_score >= 80:
        level = "high"
        confidence = min(0.5 + (total_score / 200), 0.99)
    elif total_score >= 40:
        level = "medium"
        confidence = min(0.4 + (total_score / 200), 0.85)
    else:
        level = "low"
        confidence = 0.90

    if len(text.split()) < 4 and level == "low":
        confidence = 0.6

    return {
        "level":      level,
        "score":      total_score,
        "confidence": round(confidence, 2),
        "triggers":   triggers,
        "category":   primary_category,
        "source":     "regex",
    }


# ---------------------------------------------------------------------------
# Public API — same signature as the original, fully backwards compatible
# ---------------------------------------------------------------------------
def analyze_risk(text: str) -> dict:
    """
    Assess the risk level of a support ticket.

    Flow:
      1. Regex pre-scan — fast, finds obvious trigger phrases
      2. LLM assessment — semantic, context-aware (requires ANTHROPIC_API_KEY)
      3. Fallback to weighted regex scoring if LLM unavailable

    Returns:
        {
            "level":      "high" | "medium" | "low",
            "score":      int,           # numeric score (synthetic for LLM path)
            "confidence": float,         # 0.0 - 1.0
            "triggers":   list[str],     # phrases that drove the assessment
            "category":   str,           # dominant risk category
            "source":     str,           # "llm" | "regex"
        }
    """
    if not text or not text.strip():
        return {
            "level": "low", "score": 0, "confidence": 0.5,
            "triggers": [], "category": "GENERAL", "source": "regex",
        }

    # Step 1 — regex pre-scan (always runs, populates triggers for UI display)
    regex_triggers, dominant_category = _regex_scan(text)

    # Step 2 — try LLM for semantic understanding
    llm_result = _call_llm(text)
    if llm_result:
        # Merge regex triggers into LLM result so the UI always has trigger phrases
        # LLM triggers take priority; regex triggers fill in any gaps
        merged_triggers = llm_result["triggers"][:]
        for t in regex_triggers:
            if t not in merged_triggers:
                merged_triggers.append(t)
        llm_result["triggers"] = merged_triggers
        return llm_result

    # Step 3 — fallback to weighted regex scoring
    return _fallback_score(text, regex_triggers, dominant_category)