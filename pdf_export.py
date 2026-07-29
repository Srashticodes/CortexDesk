"""
pdf_export.py — PDF generation for CortexDesk AI escalation letters.

Uses fpdf2 for lightweight PDF creation with professional formatting.
Falls back to plain-text if fpdf2 is not installed.
"""

from datetime import datetime
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
import html
from logger import get_logger

logger = get_logger(__name__)


def _clean_text_for_pdf(text: str) -> str:
    """
    Replace non-latin-1 unicode characters with safe ASCII equivalents
    and encode to latin-1 to prevent FPDFUnicodeEncodingException.
    """
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
    
    # Force encode to latin-1 (unsupported characters will be replaced by '?')
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_pdf(letter_data: dict) -> bytes | None:
    """
    Generate a professional PDF from escalation letter data.

    Args:
        letter_data: Dict with keys: subject, severity, body, timestamp, domain

    Returns:
        PDF as bytes, or None if generation fails.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        logger.warning("fpdf2 not installed — PDF export unavailable. Install with: pip install fpdf2")
        return None

    try:
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
        pdf.multi_cell(0, 7, _clean_text_for_pdf(letter_data.get("subject", "Escalation Letter")), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # --- Metadata line ---
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 116, 139)
        meta_text = (
            f"Date: {letter_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}  |  "
            f"Domain: {letter_data.get('domain', 'Unknown')}  |  "
            f"Severity: {severity}"
        )
        pdf.cell(0, 6, _clean_text_for_pdf(meta_text), new_x="LMARGIN", new_y="NEXT")

        # --- Divider ---
        pdf.ln(4)
        pdf.set_draw_color(226, 232, 240)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

        # --- Body ---
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 41, 59)

        body = letter_data.get("body", "")
        for line in body.split("\n"):
            stripped = _clean_text_for_pdf(line.strip())

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
        pdf.cell(0, 5, _clean_text_for_pdf("This document was generated automatically by CortexDesk AI."), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.cell(0, 5, _clean_text_for_pdf("For questions, contact your support operations team."), new_x="LMARGIN", new_y="NEXT", align="C")

        output = pdf.output(dest="S")
        if isinstance(output, bytes):
            return output
        if isinstance(output, bytearray):
            return bytes(output)
        return str(output).encode("latin-1", errors="replace")

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return None


def letter_to_text(letter_data: dict) -> str:
    """Return a clean plain-text letter for copy/email export."""
    subject = letter_data.get("subject", "Escalation Letter")
    body = letter_data.get("body", "").strip()
    return f"Subject: {subject}\n\n{body}".strip()


def generate_email_text(letter_data: dict) -> str:
    """Return an email-ready text version with subject and body."""
    return letter_to_text(letter_data)


def generate_docx(letter_data: dict) -> bytes:
    """
    Generate a minimal standards-compliant DOCX without external dependencies.
    Word, Google Docs, and LibreOffice can open this package.
    """
    subject = _xml_escape(letter_data.get("subject", "Escalation Letter"))
    severity = _xml_escape(letter_data.get("severity", "Medium"))
    domain = _xml_escape(letter_data.get("domain", "Unknown"))
    timestamp = _xml_escape(letter_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    body_lines = letter_data.get("body", "").splitlines()

    paragraphs = [
        _paragraph("CortexDesk AI Escalation Notice", bold=True),
        _paragraph(subject, bold=True),
        _paragraph(f"Severity: {severity} | Domain: {domain} | Generated: {timestamp}"),
    ]
    paragraphs.extend(_paragraph(_xml_escape(line)) if line.strip() else _paragraph("") for line in body_lines)

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {''.join(paragraphs)}
    <w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
  </w:body>
</w:document>"""

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def _xml_escape(value: str) -> str:
    return html.escape(_clean_text_for_pdf(str(value)), quote=True)


def _paragraph(text: str, bold: bool = False) -> str:
    bold_start = "<w:b/>" if bold else ""
    preserve = ' xml:space="preserve"' if text.startswith(" ") or text.endswith(" ") else ""
    return f"<w:p><w:r><w:rPr>{bold_start}</w:rPr><w:t{preserve}>{text}</w:t></w:r></w:p>"
