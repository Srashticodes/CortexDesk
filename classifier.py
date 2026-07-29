import json
import numpy as np
from sentence_transformers import SentenceTransformer
from llm_client import call_llm

# ---------------------------------------------------------------------------
# Domain descriptions — richer than keywords, better for semantic matching.
# Each entry is a short paragraph that describes what tickets in this domain
# look like. Add / edit these freely; they drive embedding quality.
# ---------------------------------------------------------------------------
DOMAIN_DESCRIPTIONS = {
    "Visa": (
        "Issues related to Visa credit or debit cards. Includes payment failures, "
        "unauthorized or fraudulent transactions, incorrect charges, double billing, "
        "refund requests, dispute or chargeback filings, card declined, and "
        "money deducted unexpectedly."
    ),
    "HackerRank": (
        "Issues with the HackerRank coding platform. Includes test case failures, "
        "code submission errors, compiler timeouts, wrong output, plagiarism concerns, "
        "assessment problems, contest issues, and IDE or environment bugs."
    ),
    "Claude": (
        "Issues with Anthropic's Claude AI API or Claude products. Includes rate "
        "limiting, token usage, prompt engineering, model behavior, API authentication, "
        "billing for API usage, jailbreak attempts, or harmful output concerns."
    ),
    "Apple": (
        "Issues with Apple hardware or software. Includes iPhone, MacBook, iPad, "
        "iCloud, iOS, macOS, Apple Watch, AirPods, App Store, repair requests, "
        "bricked devices, stolen devices, warranty claims, and software exploits."
    ),
    "Amazon": (
        "Issues with Amazon's marketplace or Prime service. Includes delivery problems, "
        "missing packages, wrong items, return requests, order cancellations, "
        "Prime membership issues, fake products, seller scams, and refund requests."
    ),
    "Netflix": (
        "Issues with Netflix subscriptions or streaming service. Includes billing problems, "
        "account access issues, streaming errors, device playback problems, canceled "
        "subscriptions, and account security concerns."
    ),
}

# Confidence threshold below which we call the LLM for a second opinion
LLM_FALLBACK_THRESHOLD = 0.72

# ---------------------------------------------------------------------------
# Model — loaded once at module level so it is shared across calls
# ---------------------------------------------------------------------------
_model: SentenceTransformer | None = None
_domain_embeddings: dict[str, np.ndarray] = {}


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_domain_embeddings(services: dict) -> dict[str, np.ndarray]:
    """
    Compute (and cache) one embedding per domain using DOMAIN_DESCRIPTIONS.
    Falls back to joining the config keywords if no description exists for a
    domain — so newly added services in config.yaml still work.
    """
    global _domain_embeddings
    model = _get_model()

    # Only (re-)embed domains we haven't seen yet
    for name in services:
        if name not in _domain_embeddings:
            # Priority: config.yaml description → hardcoded dict → keyword fallback
            description = (
                services[name].get("description")
                or DOMAIN_DESCRIPTIONS.get(name)
            )
            if not description:
                kws = services[name].get("keywords", [])
                description = f"Support tickets about {name}: " + ", ".join(kws)
            _domain_embeddings[name] = model.encode(description, normalize_embeddings=True)

    return _domain_embeddings


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two already-normalised vectors."""
    return float(np.dot(a, b))


# ---------------------------------------------------------------------------
# LLM fallback — routed through llm_client (supports Groq + Anthropic)
# ---------------------------------------------------------------------------
def _llm_classify(ticket_text: str, domain_names: list[str]) -> dict | None:
    """
    Ask the configured LLM to classify the ticket when embedding confidence is low.
    Returns a classification dict or None if the call fails.
    """
    domains_list = "\n".join(f"- {d}" for d in domain_names)

    system_prompt = (
        "You are a support ticket classifier. Given a customer support ticket, "
        "choose the most appropriate domain from the provided list. "
        "Respond ONLY with a JSON object — no markdown, no explanation:\n"
        '{"primary": "<domain>", "secondary": ["<domain>", ...], '
        '"confidence": <0.0-1.0>, "reason": "<one sentence>"}'
    )
    user_prompt = (
        f"Available domains:\n{domains_list}\n\n"
        f"Also list any secondary domains that apply (may be empty).\n\n"
        f"Ticket:\n{ticket_text}"
    )

    try:
        raw = call_llm(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=256)
        if not raw:
            return None
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)

        if data.get("primary") not in domain_names:
            return None

        return {
            "primary": data["primary"],
            "secondary": [d for d in data.get("secondary", []) if d in domain_names],
            "confidence": float(data.get("confidence", 0.8)),
            "source": "llm",
        }
    except Exception:
        return None   # Any failure → fall back to embedding result

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def classify_ticket(text: str, services: dict) -> dict:
    """
    Classify a support ticket using semantic embeddings.

    Returns:
        {
            "primary":    str,          # best-matching domain
            "secondary":  list[str],    # other plausible domains (score > threshold)
            "confidence": float,        # 0-1 calibrated confidence
            "source":     str,          # "embedding" | "llm" | "fallback"
        }
    """
    if not text or not text.strip():
        return {"primary": "Unknown", "secondary": [], "confidence": 0.0, "source": "fallback"}

    domain_embeddings = _get_domain_embeddings(services)
    model = _get_model()

    # Encode ticket (normalised for cosine via dot-product)
    ticket_embedding = model.encode(text.strip(), normalize_embeddings=True)

    # Score every domain
    scores: dict[str, float] = {
        domain: _cosine_similarity(ticket_embedding, emb)
        for domain, emb in domain_embeddings.items()
    }

    if not scores:
        return {"primary": "Unknown", "secondary": [], "confidence": 0.0, "source": "fallback"}

    sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary, primary_score = sorted_domains[0]

    # Secondary domains: score within 15% of primary AND above 0.35 absolute floor
    secondary_threshold = max(primary_score * 0.85, 0.35)
    secondary = [
        d for d, s in sorted_domains[1:]
        if s >= secondary_threshold
    ]

    # Calibrate confidence: map cosine score (typically 0.3-0.9) to 0-1 range
    # Clamp to [0, 1] to handle edge cases
    calibrated = round(min(max((primary_score - 0.3) / 0.6, 0.0), 1.0), 2)

    result = {
        "primary": primary,
        "secondary": secondary,
        "confidence": calibrated,
        "source": "embedding",
    }

    # Low-confidence → ask the LLM for a second opinion
    if calibrated < LLM_FALLBACK_THRESHOLD:
        llm_result = _llm_classify(text, list(services.keys()))
        if llm_result:
            return llm_result
        # LLM unavailable — mark confidence honestly
        result["confidence"] = round(calibrated * 0.9, 2)

    return result