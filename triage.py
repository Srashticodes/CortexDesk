from config import SERVICES
from classifier import classify_ticket
from risk_engine import analyze_risk
from retriever import Retriever
from responder import generate_response
from database import log_ticket
from logger import get_logger

logger = get_logger(__name__)

# Initialize Retrievers based on loaded configuration
RETRIEVERS = {}
for name, service in SERVICES.items():
    docs = service.get("docs", [])
    if docs:
        RETRIEVERS[name] = Retriever(docs, name)

def process_ticket(ticket_text):
    """
    Main orchestration function for the Triage pipeline.
    """
    if not ticket_text or not ticket_text.strip():
        logger.warning("Empty ticket received.")
        return {"error": "Ticket text cannot be empty"}

    logger.info(f"Processing ticket: {ticket_text[:50]}...")

    # Step 1: Classification
    classification = classify_ticket(ticket_text, SERVICES)
    
    if isinstance(classification, dict):
        domain = classification["primary"]
        secondary_domains = classification["secondary"]
        domain_confidence = classification["confidence"]
    else: # Fallback just in case
        domain, domain_confidence = classification
        secondary_domains = []
    
    # Combine domains for context
    all_domains = [domain] + secondary_domains if domain != "Unknown" else []
    
    # Step 2: Risk Check (Intelligence Layer)
    risk_analysis = analyze_risk(ticket_text)
    risk = risk_analysis["level"]
    risk_confidence = risk_analysis["confidence"]
    triggers = risk_analysis["triggers"]
    category = risk_analysis["category"]
    
    if domain == "Unknown":
        # Default unknown domains to higher risk if any triggers found
        if risk == "low" and triggers:
            risk = "medium"
            
    # Step 3 & 4: Decision & Response
    docs = []
    if domain in RETRIEVERS:
        docs.extend(RETRIEVERS[domain].retrieve(ticket_text))
    # Optionally add docs for secondary domains
    for sec_domain in secondary_domains:
        if sec_domain in RETRIEVERS:
            docs.extend(RETRIEVERS[sec_domain].retrieve(ticket_text))
            
    # Deduplicate docs
    docs = list(dict.fromkeys(docs))

    if risk == "high":
        decision = "escalate"
        reason = f"High Risk: Detected critical signals in {category}: {', '.join(triggers)}"
    elif risk == "medium":
        decision = "respond_and_escalate"
        reason = f"Medium Risk: Detected potential issues in {category}: {', '.join(triggers)}"
    else:
        decision = "respond"
        reason = f"Low Risk: Standard support query for {domain}."

    # Generate context-aware response
    response = generate_response(
        docs=docs,
        decision=decision,
        category=category,
        domains=all_domains,
        triggers=triggers,
        ticket=ticket_text,     # passed to LLM for context-aware drafting
    )

    # Format documents for UI
    formatted_docs = [doc.strip() for doc in docs if doc.strip()]

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
        "docs": formatted_docs
    }
    
    logger.info(f"Triage Result - Domain: {domain}, Risk: {risk}, Decision: {decision}")
    
    # Log to Database
    log_ticket(ticket_text, domain, risk, decision, reason, domain_confidence, risk_confidence)
    
    return result