from fpdf import FPDF
from datetime import datetime

letter_data = {
    'subject': 'URGENT: Potential Card Fraud — Immediate Investigation Required',
    'severity': 'Critical',
    'body': "ESCALATION NOTICE — CRITICAL PRIORITY\n==================================================\n\nDate: 2026-06-23 18:05:08\nDomain: Visa\nSeverity: Critical\nReference: CX-94854\n\nISSUE SUMMARY\n------------------------------\nA customer has reported potential unauthorized activity on their Visa card account. This requires immediate attention from the fraud investigation team.\n\nCUSTOMER REPORT\n------------------------------\nTest ticket text for Visa credit card compromise\n\nRISK INDICATORS\n------------------------------\nDetected signals: fraud\nRisk category: Security Compromise\n\nRECOMMENDED ACTIONS\n------------------------------\n  1. Initiate temporary card freeze pending investigation\n  2. Review recent transaction history for suspicious patterns\n  3. Contact the customer to verify account activity\n  4. Coordinate with the fraud prevention team for chargeback processing\n  5. File incident report per PCI DSS compliance requirements\n\nRESOLUTION TIMELINE\n------------------------------\nImmediate response required within 1 hour.\n\nThis escalation was generated automatically by CortexDesk AI based on the risk assessment of the customer's support ticket. Please review and take appropriate action.\n\n---\nCortexDesk AI — Support Intelligence Platform\nGenerated: 2026-06-23 18:05:08",
    'timestamp': '2026-06-23 18:05:08',
    'domain': 'Visa'
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "\u2014": "-",   # em dash
        "\u2013": "-",   # en dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2022": "-",   # bullet point
        "\u2122": "(TM)", # trademark
        "\xae": "(R)",    # registered
        "\xa9": "(C)",    # copyright
        "\u2026": "...",  # ellipsis
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    return text.encode("latin-1", errors="replace").decode("latin-1")

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=25)
pdf.add_page()

# --- Header ---
pdf.set_fill_color(15, 23, 42)  # slate-900
pdf.rect(0, 0, 210, 35, 'F')

pdf.set_font("Helvetica", "B", 18)
pdf.set_text_color(255, 255, 255)
pdf.set_y(8)
pdf.cell(0, 10, "CortexDesk AI", new_x="LMARGIN", new_y="NEXT", align="L")

pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(148, 163, 184)  # slate-400
pdf.cell(0, 6, "Support Intelligence Platform  |  Escalation Notice", new_x="LMARGIN", new_y="NEXT", align="L")

pdf.ln(10)

# --- Severity badge ---
severity = letter_data.get("severity", "Medium")
severity_colors = {
    "Critical": (220, 38, 38),   # red
    "High": (234, 88, 12),       # orange
    "Medium": (202, 138, 4),     # amber
}
badge_color = severity_colors.get(severity, (100, 116, 139))

pdf.set_fill_color(*badge_color)
pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(255, 255, 255)
badge_text = f"  {severity.upper()} PRIORITY  "
badge_width = pdf.get_string_width(badge_text) + 6
pdf.cell(badge_width, 8, badge_text, new_x="RIGHT", new_y="TOP", fill=True)
pdf.ln(12)

# --- Subject ---
pdf.set_font("Helvetica", "B", 14)
pdf.set_text_color(15, 23, 42)
pdf.multi_cell(0, 7, clean_text(letter_data.get("subject", "Escalation Letter")), new_x="LMARGIN", new_y="NEXT")
pdf.ln(4)

# --- Metadata line ---
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(100, 116, 139)
meta_text = (
    f"Date: {letter_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}  |  "
    f"Domain: {letter_data.get('domain', 'Unknown')}  |  "
    f"Severity: {severity}"
)
pdf.cell(0, 6, clean_text(meta_text), new_x="LMARGIN", new_y="NEXT")

# --- Divider ---
pdf.ln(4)
pdf.set_draw_color(226, 232, 240)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(6)

# --- Body ---
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(30, 41, 59)

body = letter_data.get("body", "")
for i, line in enumerate(body.split("\n")):
    stripped = clean_text(line.strip())
    print(f"Line {i}: x={pdf.get_x():.2f}, w={pdf.w:.2f}, rm={pdf.r_margin:.2f}, lm={pdf.l_margin:.2f}, text={stripped!r}")

    # Section headers (lines with dashes or equals)
    if stripped.startswith("=") or stripped.startswith("-" * 5):
        pdf.set_draw_color(203, 213, 225)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        continue

    # Bold section titles (ALL CAPS lines)
    if stripped.isupper() and len(stripped) > 3 and not stripped.startswith("CX-"):
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, stripped, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 41, 59)
        continue

    # Numbered items
    if stripped and stripped[0].isdigit() and "." in stripped[:4]:
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5.5, f"  {stripped}", new_x="LMARGIN", new_y="NEXT")
        continue

    # Regular text
    if stripped:
        pdf.multi_cell(0, 5.5, stripped, new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.ln(3)

# --- Footer ---
pdf.ln(10)
pdf.set_draw_color(226, 232, 240)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(4)

pdf.set_font("Helvetica", "I", 8)
pdf.set_text_color(148, 163, 184)
pdf.cell(0, 5, clean_text("This document was generated automatically by CortexDesk AI."), new_x="LMARGIN", new_y="NEXT", align="C")
pdf.cell(0, 5, clean_text("For questions, contact your support operations team."), new_x="LMARGIN", new_y="NEXT", align="C")

pdf.output("test.pdf")
print("Created full PDF successfully and saved to test.pdf!")
