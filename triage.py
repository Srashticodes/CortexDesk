from config import SERVICES
from risk_engine import analyze_risk
from responder import generate_response, compress_docs
from database import log_ticket
from logger import get_logger

logger = get_logger(__name__)

_RETRIEVERS = None


def _classify_fast(ticket_text: str, services: dict) -> dict:
    """Fast keyword classifier used by the interactive app by default."""
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
                score += 1
        if name.lower() in lowered:
            score += 4
        scores[name] = score

    primary, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score == 0:
        return {"primary": "Unknown", "secondary": [], "confidence": 0.45, "source": "fast_keywords"}

    secondary = [
        name for name, score in scores.items()
        if name != primary and score > 0 and score >= best_score * 0.6
    ]
    confidence = min(0.55 + (best_score * 0.08), 0.95)
    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": round(confidence, 2),
        "source": "fast_keywords",
    }


def _get_retrievers():
    """Lazy-load semantic retrievers only when slower AI mode needs them."""
    global _RETRIEVERS
    if _RETRIEVERS is None:
        from retriever import Retriever

        _RETRIEVERS = {}
        for name, service in SERVICES.items():
            docs = service.get("docs", [])
            if docs:
                _RETRIEVERS[name] = Retriever(docs, source_domain=name)
    return _RETRIEVERS


def _retrieve_fast(domain: str, ticket_text: str, top_k: int = 3) -> list[dict]:
    """Simple keyword retrieval that avoids loading the embedding model."""
    if domain not in SERVICES:
        return []

    docs = SERVICES[domain].get("docs", [])
    if not docs:
        return []

    words = {
        word.strip(".,!?;:()[]{}\"'").lower()
        for word in ticket_text.split()
        if len(word.strip(".,!?;:()[]{}\"'")) >= 4
    }

    scored = []
    for doc in docs:
        doc_text = doc.strip()
        doc_lower = doc_text.lower()
        hits = sum(1 for word in words if word in doc_lower)
        if hits:
            scored.append({
                "text": doc_text,
                "score": round(min(0.3 + hits * 0.1, 0.95), 3),
                "source": domain,
                "reason": f"Matched {hits} keyword(s) from the ticket in the {domain} knowledge base.",
            })

    if not scored:
        scored = [{
            "text": doc.strip(),
            "score": 0.25,
            "source": domain,
            "reason": f"Included a general {domain} knowledge-base note.",
        } for doc in docs[:top_k] if doc.strip()]

    return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]


def process_ticket(ticket_text: str, use_ai: bool = False):
    """
    Main orchestration function for the triage pipeline.
    Fast mode is local and responsive; AI mode uses the richer LLM/embedding path.
    """
    if not ticket_text or not ticket_text.strip():
        logger.warning("Empty ticket received.")
        return {"error": "Ticket text cannot be empty"}

    logger.info(f"Processing ticket: {ticket_text[:50]}...")

    combined = None
    analysis_source = "unknown"
    if use_ai:
        from analyzer import analyze_ticket
        combined = analyze_ticket(ticket_text, SERVICES)

    if combined:
        domain = combined["domain"]["primary"]
        secondary_domains = combined["domain"]["secondary"]
        domain_confidence = combined["domain"]["confidence"]
        risk = combined["risk"]["level"]
        risk_confidence = combined["risk"]["confidence"]
        triggers = combined["risk"]["triggers"]
        category = combined["risk"]["category"]
        analysis_source = "combined_llm"
        logger.info("Used combined analyzer (1 LLM call)")
    else:
        if use_ai:
            logger.info("Combined analyzer failed, falling back to separate calls")
            from classifier import classify_ticket
            classification = classify_ticket(ticket_text, SERVICES)
        else:
            logger.info("Using fast local analysis")
            classification = _classify_fast(ticket_text, SERVICES)

        domain = classification["primary"]
        secondary_domains = classification["secondary"]
        domain_confidence = classification["confidence"]
        analysis_source = f"separate_{classification.get('source', 'fast_keywords')}"

        risk_analysis = analyze_risk(ticket_text, use_ai=use_ai)
        risk = risk_analysis["level"]
        risk_confidence = risk_analysis["confidence"]
        triggers = risk_analysis["triggers"]
        category = risk_analysis["category"]

    all_domains = [domain] + secondary_domains if domain != "Unknown" else []

    if domain == "Unknown" and risk == "low" and triggers:
        risk = "medium"

    docs = []
    scored_docs = []
    retrievers = _get_retrievers() if use_ai else {}

    if use_ai and domain in retrievers:
        domain_scored = retrievers[domain].retrieve_with_scores(ticket_text)
    else:
        domain_scored = _retrieve_fast(domain, ticket_text)

    scored_docs.extend(domain_scored)
    docs.extend([d["text"] for d in domain_scored])

    for sec_domain in secondary_domains:
        if use_ai and sec_domain in retrievers:
            sec_scored = retrievers[sec_domain].retrieve_with_scores(ticket_text)
        else:
            sec_scored = _retrieve_fast(sec_domain, ticket_text, top_k=1)
        scored_docs.extend(sec_scored)
        docs.extend([d["text"] for d in sec_scored])

    seen_texts = set()
    unique_docs = []
    unique_scored = []
    for i, doc_text in enumerate(docs):
        if doc_text not in seen_texts:
            seen_texts.add(doc_text)
            unique_docs.append(doc_text)
            if i < len(scored_docs):
                unique_scored.append(scored_docs[i])

    docs = unique_docs
    scored_docs = unique_scored

    if scored_docs:
        scored_docs = sorted(scored_docs, key=lambda item: item.get("score", 0), reverse=True)
        compressed_texts = compress_docs([d["text"] for d in scored_docs], max_docs=3, max_chars=2200)
        filtered_scored = []
        for item in scored_docs:
            if item.get("text") in compressed_texts and item.get("text") not in [d.get("text") for d in filtered_scored]:
                filtered_scored.append(item)
                if len(filtered_scored) >= 3:
                    break
        scored_docs = filtered_scored
        docs = [d["text"] for d in scored_docs]

    if risk == "high":
        decision = "escalate"
        reason = f"High Risk: Detected critical signals in {category}: {', '.join(triggers) or 'high-priority issue'}"
    elif risk == "medium":
        decision = "respond_and_escalate"
        reason = f"Medium Risk: Detected potential issues in {category}: {', '.join(triggers) or 'review recommended'}"
    else:
        decision = "respond"
        reason = f"Low Risk: Standard support query for {domain}."

    response = generate_response(
        docs=docs,
        decision=decision,
        category=category,
        domains=all_domains,
        triggers=triggers,
        ticket=ticket_text,
    )

    formatted_docs = [doc.strip() for doc in docs if doc.strip()]
    retrieval_scores_str = "; ".join(
        f"{d.get('source', '?')}:{d.get('score', 0):.2f}" for d in scored_docs
    )

    result = {
        "ticket": ticket_text,
        "domain": domain,
        "secondary_domains": secondary_domains,
        "domain_confidence": domain_confidence,
        "risk": risk,
        "risk_confidence": risk_confidence,
        "decision": decision,
        "reason": reason,
        "triggers": triggers,
        "category": category,
        "response": response,
        "docs": formatted_docs,
        "scored_docs": scored_docs,
        "analysis_source": analysis_source,
        "retrieval_explanation": _build_retrieval_explanation(scored_docs, domain),
    }

    logger.info(f"Triage Result - Domain: {domain}, Risk: {risk}, Decision: {decision}, Source: {analysis_source}")

    ticket_id = log_ticket(
        ticket_text, domain, risk, decision, reason,
        domain_confidence, risk_confidence,
        response=response,
        category=category,
        triggers=triggers,
        analysis_source=analysis_source,
        retrieval_scores=retrieval_scores_str,
    )
    result["ticket_id"] = ticket_id

    return result


def _build_retrieval_explanation(scored_docs: list[dict], primary_domain: str) -> str:
    """Build a human-readable explanation of why these documents were retrieved."""
    if not scored_docs:
        return "No relevant knowledge base documents were found for this query."

    parts = [f"Retrieved {len(scored_docs)} document(s) from the knowledge base."]

    domains_used = set(d.get("source", "") for d in scored_docs if d.get("source"))
    if domains_used:
        parts.append(f"Sources: {', '.join(sorted(domains_used))}.")

    avg_score = sum(d.get("score", 0) for d in scored_docs) / len(scored_docs)
    if avg_score >= 0.5:
        parts.append("Overall relevance: High - documents closely match the query context.")
    elif avg_score >= 0.35:
        parts.append("Overall relevance: Moderate - documents are related but may not cover all aspects.")
    else:
        parts.append("Overall relevance: Low - limited matching content found in the knowledge base.")

    return " ".join(parts)
