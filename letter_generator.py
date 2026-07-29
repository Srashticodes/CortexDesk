"""
Professional letter generation for CortexDesk.

The default path is template based so letters appear instantly. AI generation is
available only when the UI's slower AI toggle is enabled.
"""

import json
import hashlib
from datetime import datetime
from llm_client import call_llm
from logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a professional customer support escalation specialist. Generate a formal letter that can be sent directly to the company responsible for resolving the customer's issue.

The letter should include:
1. Subject line
2. Formal salutation addressed to the company's support or escalation team
3. Brief issue summary
4. Severity and impact
5. Specific requested actions
6. Requested response timeline
7. Professional closing

Rules:
- Professional, formal tone throughout
- No emojis or casual language
- Include specific details from the ticket
- Write from the customer's perspective or on behalf of the customer
- Do not describe the letter as internal-only
- Be concise but complete

Return ONLY a JSON object:
{
  "subject": "<subject line>",
  "severity": "Critical" | "High" | "Medium",
  "body": "<full letter body in plain text with newlines>"
}"""


DOMAIN_TEMPLATES = {
    "Visa": {
        "SECURITY_COMPROMISE": {
            "subject": "Urgent Request for Investigation of Potential Unauthorized Card Activity",
            "preamble": "The customer has reported possible unauthorized activity on their Visa card account.",
            "actions": [
                "Temporarily secure or block the affected card if needed",
                "Review recent transactions for unauthorized activity",
                "Initiate dispute or chargeback handling for confirmed suspicious charges",
                "Provide written confirmation of the investigation outcome",
            ],
        },
        "BILLING_ISSUE": {
            "subject": "Formal Request for Review of Billing Dispute",
            "preamble": "The customer has reported a billing discrepancy that requires review and resolution.",
            "actions": [
                "Review the disputed transaction records",
                "Confirm whether duplicate or incorrect charges occurred",
                "Process any refund or adjustment that is due",
                "Provide a clear written explanation of the resolution",
            ],
        },
    },
    "Amazon": {
        "SECURITY_COMPROMISE": {
            "subject": "Urgent Request for Amazon Account Security Review",
            "preamble": "The customer has reported a possible security issue affecting their Amazon account.",
            "actions": [
                "Secure the affected account and verify recent login activity",
                "Review recent orders, payment activity, and address changes",
                "Reverse or cancel any unauthorized activity where applicable",
                "Confirm the remediation steps taken in writing",
            ],
        },
        "BILLING_ISSUE": {
            "subject": "Formal Request for Amazon Order or Refund Resolution",
            "preamble": "The customer has raised an order, refund, or billing concern that requires escalation.",
            "actions": [
                "Review the order history and delivery status",
                "Process the appropriate refund, replacement, or correction",
                "Investigate seller or product concerns where relevant",
                "Provide a written resolution timeline",
            ],
        },
    },
    "Apple": {
        "SECURITY_COMPROMISE": {
            "subject": "Urgent Request for Apple Account or Device Security Review",
            "preamble": "The customer has reported a possible security incident involving an Apple account or device.",
            "actions": [
                "Review Apple ID and iCloud account activity",
                "Secure the account and guide the customer through recovery steps",
                "Review unauthorized purchases or suspicious access",
                "Provide written confirmation of the protective actions taken",
            ],
        },
        "TECH_ISSUE": {
            "subject": "Formal Request for Escalated Apple Technical Support",
            "preamble": "The customer has reported a significant technical issue requiring advanced review.",
            "actions": [
                "Review diagnostics and the reported failure details",
                "Confirm warranty, repair, or replacement eligibility",
                "Provide a practical workaround if immediate repair is not available",
                "Share the next steps and expected resolution timeline",
            ],
        },
    },
    "HackerRank": {
        "SECURITY_COMPROMISE": {
            "subject": "Formal Request for HackerRank Platform Integrity Review",
            "preamble": "The customer has reported a potential platform integrity or assessment concern.",
            "actions": [
                "Review the affected assessment or submission records",
                "Check for platform, plagiarism, or access-related anomalies",
                "Notify relevant stakeholders if assessment integrity was affected",
                "Provide a documented outcome and next steps",
            ],
        },
        "TECH_ISSUE": {
            "subject": "Formal Request for HackerRank Technical Issue Resolution",
            "preamble": "The customer has reported a technical issue that may have affected platform use.",
            "actions": [
                "Review logs for the reported issue",
                "Assess whether the issue affected assessment results",
                "Provide a reattempt or correction where appropriate",
                "Escalate confirmed platform defects to engineering",
            ],
        },
    },
    "Claude": {
        "SECURITY_COMPROMISE": {
            "subject": "Formal Request for Claude API Safety and Account Review",
            "preamble": "The customer has reported a potential safety, access, or misuse concern involving Claude.",
            "actions": [
                "Review account and API usage logs",
                "Assess whether account security or policy issues are involved",
                "Apply protective measures if warranted",
                "Provide written confirmation of findings and next steps",
            ],
        },
        "BILLING_ISSUE": {
            "subject": "Formal Request for Claude API Billing Review",
            "preamble": "The customer has raised a billing or usage concern requiring account-level review.",
            "actions": [
                "Review usage and billing calculations",
                "Verify the charges against the applicable plan",
                "Process any credit or correction that is due",
                "Provide a written explanation of the billing outcome",
            ],
        },
    },
    "Netflix": {
        "SECURITY_COMPROMISE": {
            "subject": "Urgent Request for Netflix Account Security Review",
            "preamble": "The customer has reported a possible security concern affecting their Netflix account.",
            "actions": [
                "Review recent account activity and device access",
                "Secure the account and verify the customer's recovery details",
                "Investigate any unauthorized subscription or viewing activity",
                "Provide written confirmation of the remediation steps",
            ],
        },
        "BILLING_ISSUE": {
            "subject": "Formal Request for Netflix Billing or Subscription Review",
            "preamble": "The customer has raised a billing or subscription issue that requires review.",
            "actions": [
                "Review the subscription and billing history",
                "Verify whether any duplicate or incorrect charges occurred",
                "Process any applicable refund or account correction",
                "Provide a written update on the resolution timeline",
            ],
        },
    },
}


def _get_default_template(domain: str, category: str) -> dict:
    domain_templates = DOMAIN_TEMPLATES.get(domain, {})
    template = domain_templates.get(category)
    if template:
        return template

    return {
        "subject": f"Formal Request for {domain} Support Review and Resolution",
        "preamble": f"The customer has reported an issue involving {domain} that requires review by the appropriate support team.",
        "actions": [
            "Review the customer's report and account history",
            "Assess the severity and customer impact",
            "Apply the appropriate remedy or escalation path",
            "Provide a written update with the resolution timeline",
        ],
    }


def generate_letter(
    ticket_text: str,
    domain: str,
    risk: str,
    decision: str,
    triggers: list[str],
    response: str,
    category: str,
    use_ai: bool = False,
) -> dict:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    severity_map = {"high": "Critical", "medium": "High", "low": "Medium"}
    severity = severity_map.get(risk, "Medium")

    if use_ai:
        llm_letter = _generate_via_llm(ticket_text, domain, risk, decision, triggers, category, severity)
        if llm_letter:
            llm_letter["timestamp"] = timestamp
            llm_letter["domain"] = domain
            llm_letter["reference_number"] = _reference_number(ticket_text)
            logger.info(f"Generated company letter via LLM for domain: {domain}")
            return llm_letter

    logger.info(f"Generated company letter via template for domain: {domain}")
    return _generate_from_template(ticket_text, domain, risk, triggers, category, severity, timestamp)


def _generate_via_llm(
    ticket_text: str,
    domain: str,
    risk: str,
    decision: str,
    triggers: list[str],
    category: str,
    severity: str,
) -> dict | None:
    triggers_text = ", ".join(triggers) if triggers else "none identified"
    user_prompt = f"""Ticket Text:
\"\"\"{ticket_text}\"\"\"

Analysis Context:
- Company/Domain: {domain}
- Risk Level: {risk}
- Severity: {severity}
- Decision: {decision}
- Risk Category: {category}
- Trigger Phrases: {triggers_text}

Generate the ready-to-send company letter now."""

    try:
        raw = call_llm(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt, max_tokens=650)
        if not raw:
            return None

        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        body = data.get("body", "").strip()
        if not body:
            return None

        return {
            "subject": data.get("subject", "Formal Support Escalation Request"),
            "severity": data.get("severity", severity),
            "body": body,
        }
    except Exception:
        return None


def _generate_from_template(
    ticket_text: str,
    domain: str,
    risk: str,
    triggers: list[str],
    category: str,
    severity: str,
    timestamp: str,
) -> dict:
    template = _get_default_template(domain, category)
    triggers_text = ", ".join(triggers) if triggers else "automated support risk assessment"
    reference_number = _reference_number(ticket_text)

    ticket_summary = ticket_text.strip()[:500]
    if len(ticket_text.strip()) > 500:
        ticket_summary += "..."

    actions_text = "\n".join(f"{i + 1}. {action}" for i, action in enumerate(template["actions"]))
    timeline = (
        "Please acknowledge this request and begin immediate action within 1 hour."
        if severity == "Critical"
        else "Please acknowledge this request and provide a substantive update within 4 business hours."
        if severity == "High"
        else "Please acknowledge this request and provide a resolution update within 24 business hours."
    )

    body = f"""Date: {timestamp}
Reference Number: {reference_number}

To: {domain} Customer Support / Escalation Team

Dear {domain} Support Team,

I am writing to formally request review and resolution of the issue described below.

Issue Summary
{template["preamble"]}

Customer Report
{ticket_summary}

Severity and Risk Indicators
Severity: {severity}
Detected signals: {triggers_text}
Risk category: {category.replace("_", " ").title()}

Supporting Evidence
Reference number: {reference_number}
Original report timestamp: {timestamp}
Automated decision: {risk.title()} risk / {category.replace("_", " ").title()}

Requested Actions
{actions_text}

Requested Resolution
Please investigate the report, apply the appropriate remedy, and provide written confirmation of the outcome.

Requested Timeline
{timeline}

Recommended Next Steps
1. Confirm receipt of this escalation.
2. Assign the matter to the appropriate specialist team.
3. Share a written status update and resolution timeline.
4. Request any additional verification or documentation from the customer if required.

If further verification or documentation is required, please contact the customer promptly using the registered contact details on the account.

Sincerely,
Customer Support Escalation Desk"""

    return {
        "subject": template["subject"],
        "severity": severity,
        "body": body,
        "timestamp": timestamp,
        "domain": domain,
        "reference_number": reference_number,
    }


def _reference_number(ticket_text: str) -> str:
    digest = hashlib.sha1(ticket_text.strip().encode("utf-8")).hexdigest()
    return f"CX-{digest[:8].upper()}"
