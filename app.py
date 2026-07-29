"""
app.py — CortexDesk AI — Support Intelligence Platform
Complete Streamlit frontend with premium SaaS-grade UI.
"""

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import json
import os
import html
from datetime import datetime

from ui_components import (
    inject_global_css, render_page_header, render_metric_card,
    render_risk_badge, render_risk_badge_standalone, render_decision_badge,
    render_decision_badge_standalone, render_confidence_bars, render_confidence_bar,
    render_ticket_card, render_doc_snippet, render_trigger_tags,
    render_explainability_panel, render_empty_state, render_status_indicator,
    render_activity_item, render_letter_preview,
    render_risk_distribution_bar, render_bulk_progress_summary,
    render_sidebar_logo, render_sidebar_footer, render_sidebar_nav_label,
    render_upload_zone_instructions, render_analytics_header,
    render_chart_card, render_command_bar,
)
from triage import process_ticket
from database import init_db, get_history, save_escalation_letter, get_user_letters
from auth import (
    init_users_db, signup, login, get_user, increment_user_stat,
    get_security_question, verify_security_answer, reset_password,
    validate_session, logout_session,
)
from letter_generator import generate_letter
from pdf_export import generate_pdf, generate_docx, generate_email_text, letter_to_text
from llm_client import get_call_stats
from logger import get_logger

logger = get_logger(__name__)



def _safe(value) -> str:
    return html.escape(str(value), quote=True)


def _letter_key(ticket_id, letter: dict) -> str:
    return f"{ticket_id or 'unsaved'}::{letter.get('subject', '')}::{len(letter.get('body', ''))}"


def _save_letter_once(ticket_id, letter: dict):
    key = _letter_key(ticket_id, letter)
    saved_keys = st.session_state.setdefault("saved_letter_keys", set())
    if key in saved_keys:
        return
    if ticket_id:
        save_escalation_letter(
            ticket_id=ticket_id,
            subject=letter["subject"],
            body=letter["body"],
            severity=letter["severity"],
            domain=letter["domain"],
            generated_by=st.session_state.current_user or "",
        )
    if st.session_state.current_user:
        increment_user_stat(st.session_state.current_user, "total_letters_generated")
    saved_keys.add(key)


def _render_letter_exports(letter: dict):
    plain_text = letter_to_text(letter)
    email_text = generate_email_text(letter)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = str(letter.get("domain", "ticket")).lower().replace(" ", "_")

    tabs = st.tabs(["Preview", "Copy", "Email"])
    with tabs[0]:
        render_letter_preview(letter)
    with tabs[1]:
        st.text_area("Copy-ready letter", value=plain_text, height=320, label_visibility="collapsed")
    with tabs[2]:
        st.text_area("Email-ready version", value=email_text, height=320, label_visibility="collapsed")

    pdf_bytes = generate_pdf(letter)
    docx_bytes = generate_docx(letter)
    d1, d2 = st.columns(2)
    with d1:
        if pdf_bytes:
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"cortexdesk_escalation_{domain}_{timestamp}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
                key=f"pdf_{timestamp}_{domain}",
            )
        else:
            st.error("PDF export requires fpdf2. Install it with: pip install fpdf2")
    with d2:
        st.download_button(
            label="Download DOCX",
            data=docx_bytes,
            file_name=f"cortexdesk_escalation_{domain}_{timestamp}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            key=f"docx_{timestamp}_{domain}",
        )


# ─── Setup ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CortexDesk AI — Support Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_db()
init_users_db()
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
inject_global_css(st.session_state.dark_mode)


# ═══════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "session_token" not in st.session_state:
    st.session_state.session_token = ""
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"

if not st.session_state.authenticated:
    persisted_token = st.query_params.get("session", "")
    if persisted_token:
        restored_user = validate_session(persisted_token)
        if restored_user:
            st.session_state.authenticated = True
            st.session_state.current_user = restored_user["username"]
            st.session_state.session_token = persisted_token

if not st.session_state.authenticated:
    # ── Auth brand mark + title ──────────────────────────────────────────
    st.markdown("""
    <div style="text-align: center; margin-top: 44px; margin-bottom: 28px;">
        <div class="cx-auth-logo-mark" style="margin: 0 auto 14px auto;">C</div>
        <h1 style="font-size: 26px; font-weight: 800; color: var(--text-primary);
                   margin: 0; letter-spacing: -1px;">CortexDesk AI</h1>
        <p style="color: var(--text-tertiary); font-size: 13.5px; margin-top: 6px; font-weight: 500;">
            Support Intelligence Platform
        </p>
    </div>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([1.0, 1.8, 1.0])

    with center_col:
        # ── LOGIN ──────────────────────────────────────────────────────
        if st.session_state.auth_page == "login":
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                remember_me = st.checkbox("Keep me signed in")
                submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                if submitted:
                    result = login(username, password, remember_me=remember_me)
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.current_user = result["user"]["username"]
                        st.session_state.session_token = result["token"]
                        if remember_me:
                            st.query_params["session"] = result["token"]
                        elif "session" in st.query_params:
                            del st.query_params["session"]
                        st.rerun()
                    else:
                        st.error(result["message"])

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Create account", use_container_width=True):
                    st.session_state.auth_page = "signup"
                    st.rerun()
            with col_b:
                if st.button("Forgot password?", use_container_width=True):
                    st.session_state.auth_page = "forgot"
                    st.rerun()

        # ── SIGNUP ─────────────────────────────────────────────────────
        elif st.session_state.auth_page == "signup":
            with st.form("signup_form", clear_on_submit=False):
                st.markdown("""
                <div style="font-size: 18px; font-weight: 800; color: var(--text-primary);
                            margin-bottom: 4px; letter-spacing: -0.5px;">Create account</div>
                <div style="font-size: 13px; color: var(--text-tertiary); margin-bottom: 18px;">
                    Set up your CortexDesk workspace
                </div>
                """, unsafe_allow_html=True)
                new_username = st.text_input("Username", placeholder="Choose a username")
                new_email = st.text_input("Email", placeholder="you@company.com")
                new_password = st.text_input(
                    "Password", type="password",
                    placeholder="Min 8 chars, letter + digit",
                    help="At least 8 characters with at least one letter and one digit."
                )
                sec_q = st.text_input("Security Question (optional)", placeholder="e.g., What is your pet's name?")
                sec_a = st.text_input("Security Answer (optional)", placeholder="Your answer")
                signup_submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

                if signup_submitted:
                    result = signup(new_username, new_email, new_password, sec_q, sec_a)
                    if result["success"]:
                        st.success(result["message"] + " Please sign in.")
                        st.session_state.auth_page = "login"
                        st.rerun()
                    else:
                        st.error(result["message"])

            if st.button("← Back to Sign In", use_container_width=True):
                st.session_state.auth_page = "login"
                st.rerun()

        # ── FORGOT PASSWORD ────────────────────────────────────────────
        elif st.session_state.auth_page == "forgot":
            st.markdown("""
            <div style="font-size: 18px; font-weight: 800; color: var(--text-primary);
                        margin-bottom: 4px; letter-spacing: -0.5px;">Reset password</div>
            <div style="font-size: 13px; color: var(--text-tertiary); margin-bottom: 18px;">
                Verify your identity to set a new password
            </div>
            """, unsafe_allow_html=True)

            if "reset_verified" not in st.session_state:
                st.session_state.reset_verified = False
            if "reset_username" not in st.session_state:
                st.session_state.reset_username = ""

            if not st.session_state.reset_verified:
                with st.form("forgot_form"):
                    reset_user = st.text_input("Username", placeholder="Enter your username")
                    reset_answer = st.text_input("Security Answer", type="password", placeholder="Enter your security answer")
                    verify_btn = st.form_submit_button("Verify Identity", use_container_width=True, type="primary")

                    if verify_btn:
                        sec_question = get_security_question(reset_user)
                        if not sec_question:
                            st.error("No security question found for this account.")
                        elif verify_security_answer(reset_user, reset_answer):
                            st.session_state.reset_verified = True
                            st.session_state.reset_username = reset_user
                            st.rerun()
                        else:
                            st.error("Incorrect security answer.")
            else:
                with st.form("reset_form"):
                    new_pw = st.text_input("New Password", type="password", placeholder="Enter your new password")
                    reset_btn = st.form_submit_button("Reset Password", use_container_width=True, type="primary")

                    if reset_btn:
                        result = reset_password(st.session_state.reset_username, new_pw)
                        if result["success"]:
                            st.success("Password reset successfully. Please sign in.")
                            st.session_state.reset_verified = False
                            st.session_state.reset_username = ""
                            st.session_state.auth_page = "login"
                            st.rerun()
                        else:
                            st.error(result["message"])

            if st.button("← Back to Sign In", use_container_width=True, key="back_forgot"):
                st.session_state.reset_verified = False
                st.session_state.reset_username = ""
                st.session_state.auth_page = "login"
                st.rerun()

    # ── Auth footer ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align: center; margin-top: 32px; font-size: 11.5px; color: var(--text-tertiary);">
        CortexDesk AI &mdash; Enterprise Support Intelligence &mdash; All data processed securely
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    render_sidebar_logo()

    st.toggle("Dark mode", value=st.session_state.dark_mode, key="dark_mode",
              help="Switch between the premium dark and light CortexDesk themes.")

    st.markdown("---")

    render_sidebar_nav_label("Navigation")

    NAV_ICONS = {
        "Dashboard":      "◈",
        "Analyze Ticket": "◉",
        "History":        "▤",
        "Analytics":      "◎",
        "Bulk Upload":    "⊞",
        "Profile":        "◷",
    }
    nav_options = list(NAV_ICONS.keys())

    page = st.radio(
        "Navigation",
        nav_options,
        format_func=lambda x: f"{NAV_ICONS.get(x, '')}  {x}",
        label_visibility="collapsed",
    )

    st.markdown("---")

    # System status
    render_sidebar_nav_label("System")
    llm_provider = os.environ.get("LLM_PROVIDER", "groq").title()
    api_key_set = bool(os.environ.get("GROQ_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))
    render_status_indicator(f"LLM: {llm_provider}", "online" if api_key_set else "offline")

    # Current user card
    user = st.session_state.current_user or "User"
    initials = user[0].upper() if user else "U"
    st.markdown(f"""
    <div style="margin-top: 14px; padding: 12px 14px;
                background: rgba(45,212,191,0.05);
                border: 1px solid rgba(45,212,191,0.12);
                border-radius: 10px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 30px; height: 30px;
                        background: linear-gradient(135deg, #2dd4bf, #38bdf8);
                        border-radius: 50%;
                        display: flex; align-items: center; justify-content: center;
                        color: #07111f; font-weight: 800; font-size: 13px;
                        flex-shrink: 0;">{_safe(initials)}</div>
            <div>
                <div style="font-size: 13px; font-weight: 700; color: #e2f0fb;">{_safe(user)}</div>
                <div style="font-size: 11px; color: #4a6480; margin-top: 1px;">Active session</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    if st.button("Sign Out", use_container_width=True):
        logout_session(st.session_state.get("session_token", ""))
        if "session" in st.query_params:
            del st.query_params["session"]
        st.session_state.authenticated = False
        st.session_state.current_user = None
        for key in list(st.session_state.keys()):
            if key not in ("authenticated", "current_user", "auth_page"):
                del st.session_state[key]
        st.rerun()

    render_sidebar_footer("v1.0")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

if page == "Dashboard":
    render_page_header("Dashboard", "AI-powered support intelligence overview")

    history_df = get_history()

    if history_df.empty:
        render_empty_state(
            "No tickets processed yet",
            "Head to Analyze Ticket or Bulk Upload to get started. Your insights will appear here.",
        )
    else:
        total_tickets = len(history_df)
        escalated = len(history_df[history_df["decision"] == "escalate"])
        responded_escalated = len(history_df[history_df["decision"] == "respond_and_escalate"])
        auto_responded = len(history_df[history_df["decision"] == "respond"])
        escalation_rate = ((escalated + responded_escalated) / total_tickets) * 100 if total_tickets > 0 else 0
        high_risk = len(history_df[history_df["risk"] == "high"])

        # ── Command bar ──────────────────────────────────────────────────────
        llm_provider = os.environ.get("LLM_PROVIDER", "groq").title()
        api_key_set = bool(os.environ.get("GROQ_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))
        render_command_bar(
            user=st.session_state.current_user or "User",
            provider=f"LLM: {llm_provider}",
            online=api_key_set,
            page="Dashboard",
        )

        # ── KPI Row ──────────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card("Total Tickets", total_tickets, "Processed to date")
        with c2:
            render_metric_card("Auto-Responded", auto_responded, "Handled by AI", color="var(--risk-low)")
        with c3:
            render_metric_card("Escalation Rate", f"{escalation_rate:.1f}%", "Escalate + Respond & Escalate")
        with c4:
            render_metric_card("High Risk", high_risk, "Critical tickets detected", color="var(--risk-critical)")

        st.markdown("")

        # ── Two-column layout ────────────────────────────────────────────────
        col_left, col_right = st.columns([1.1, 1])

        with col_left:
            st.markdown('<div class="cx-section-title">Risk Distribution</div>', unsafe_allow_html=True)
            risk_counts = history_df["risk"].value_counts()
            low_count  = int(risk_counts.get("low", 0))
            med_count  = int(risk_counts.get("medium", 0))
            high_count = int(risk_counts.get("high", 0))
            render_risk_distribution_bar(low_count, med_count, high_count)

            st.markdown('<div class="cx-section-title">Domain Breakdown</div>', unsafe_allow_html=True)
            st.markdown('<div class="cx-card-compact">', unsafe_allow_html=True)
            domain_counts = history_df["domain"].value_counts().reset_index()
            domain_counts.columns = ["Domain", "Count"]
            st.bar_chart(domain_counts.set_index("Domain"), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_right:
            st.markdown('<div class="cx-section-title">Recent Activity</div>', unsafe_allow_html=True)
            st.markdown('<div class="cx-card-compact">', unsafe_allow_html=True)
            recent = history_df.head(8)
            for _, row in recent.iterrows():
                ticket_text = str(row.get("ticket_text", ""))
                display = ticket_text[:85] + "..." if len(ticket_text) > 85 else ticket_text
                risk_val   = row.get("risk", "low")
                domain_val = row.get("domain", "Unknown")
                ts = str(row.get("timestamp", ""))
                render_activity_item(
                    f"[{domain_val}] {display}",
                    timestamp=ts,
                    risk=risk_val,
                )
            st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: ANALYZE TICKET
# ═══════════════════════════════════════════════════════════════════════════

elif page == "Analyze Ticket":
    render_page_header(
        "Analyze Ticket",
        "Submit a support ticket for AI-powered classification, risk assessment, and response generation"
    )

    col_input, col_result = st.columns([1, 1.25])

    with col_input:
        st.markdown('<div class="cx-section-title">Ticket Input</div>', unsafe_allow_html=True)

        with st.form("analyze_form"):
            ticket = st.text_area(
                "Ticket Content",
                height=195,
                placeholder="Paste or type the customer support ticket here...\n\ne.g., My Visa card was charged for an unauthorized transaction of $500 yesterday.",
                label_visibility="collapsed",
            )
            use_ai = st.toggle(
                "AI-enhanced analysis",
                value=False,
                help="Off uses fast local rules. On uses LLM + semantic retrieval when keys are configured.",
            )
            auto_letter = st.toggle(
                "Auto-generate escalation letter",
                value=False,
                help="Generates a PDF-ready letter when a ticket is high risk and escalated.",
            )
            submitted = st.form_submit_button("Analyze Ticket", type="primary", use_container_width=True)

        # ── Domain pills ────────────────────────────────────────────────────
        st.markdown("""
        <div style="margin-top: 14px;">
            <div style="font-size: 11.5px; color: var(--text-tertiary); margin-bottom: 8px; font-weight: 600;
                        text-transform: uppercase; letter-spacing: 0.5px;">Supported Domains</div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                <span style="display: inline-block; padding: 3px 10px; background: var(--accent-subtle);
                             color: var(--accent); border-radius: 999px; font-size: 12px; font-weight: 600;
                             border: 1px solid rgba(45,212,191,0.18);">Visa</span>
                <span style="display: inline-block; padding: 3px 10px; background: var(--accent-subtle);
                             color: var(--accent); border-radius: 999px; font-size: 12px; font-weight: 600;
                             border: 1px solid rgba(45,212,191,0.18);">Amazon</span>
                <span style="display: inline-block; padding: 3px 10px; background: var(--accent-subtle);
                             color: var(--accent); border-radius: 999px; font-size: 12px; font-weight: 600;
                             border: 1px solid rgba(45,212,191,0.18);">Apple</span>
                <span style="display: inline-block; padding: 3px 10px; background: var(--accent-subtle);
                             color: var(--accent); border-radius: 999px; font-size: 12px; font-weight: 600;
                             border: 1px solid rgba(45,212,191,0.18);">HackerRank</span>
                <span style="display: inline-block; padding: 3px 10px; background: var(--accent-subtle);
                             color: var(--accent); border-radius: 999px; font-size: 12px; font-weight: 600;
                             border: 1px solid rgba(45,212,191,0.18);">Claude</span>
                <span style="display: inline-block; padding: 3px 10px; background: var(--accent-subtle);
                             color: var(--accent); border-radius: 999px; font-size: 12px; font-weight: 600;
                             border: 1px solid rgba(45,212,191,0.18);">Netflix</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_result:
        if submitted:
            if not ticket.strip():
                st.error("Please enter a ticket before analyzing.")
                st.session_state.pop("last_result", None)
            else:
                with st.spinner("Analyzing ticket..."):
                    result = process_ticket(ticket, use_ai=use_ai)

                if st.session_state.current_user:
                    increment_user_stat(st.session_state.current_user, "total_tickets_analyzed")
                    if result.get("decision") in ("escalate", "respond_and_escalate"):
                        increment_user_stat(st.session_state.current_user, "total_escalations")

                st.session_state.last_result = result
                st.session_state.last_letter = None
                st.session_state.last_letter_ticket_id = None
                letter_allowed = result.get("decision") in ("escalate", "respond_and_escalate")

                if auto_letter and letter_allowed:
                    with st.spinner("Generating escalation letter..."):
                        letter = generate_letter(
                            ticket_text=result["ticket"],
                            domain=result["domain"],
                            risk=result["risk"],
                            decision=result["decision"],
                            triggers=result.get("triggers", []),
                            response=result.get("response", ""),
                            category=result.get("category", "GENERAL"),
                            use_ai=use_ai,
                        )
                    st.session_state.last_letter = letter
                    st.session_state.last_letter_ticket_id = result.get("ticket_id")
                    _save_letter_once(result.get("ticket_id"), letter)

        result = st.session_state.get("last_result")

        if result:
            letter_allowed = result.get("decision") in ("escalate", "respond_and_escalate")

            st.markdown('<div class="cx-section-title">Analysis Results</div>', unsafe_allow_html=True)

            # ── Key metrics ──────────────────────────────────────────────────
            r1, r2, r3 = st.columns(3)

            domain_text = result["domain"]
            if result.get("secondary_domains"):
                domain_text += f" +{len(result['secondary_domains'])}"

            with r1:
                st.markdown(f"""
                <div class="cx-result-item">
                    <div class="cx-result-label">Domain</div>
                    <div class="cx-result-value">{_safe(domain_text)}</div>
                </div>
                """, unsafe_allow_html=True)
            with r2:
                st.markdown(f"""
                <div class="cx-result-item">
                    <div class="cx-result-label">Risk Level</div>
                    <div style="margin-top: 6px;">{render_risk_badge(result["risk"])}</div>
                </div>
                """, unsafe_allow_html=True)
            with r3:
                st.markdown(f"""
                <div class="cx-result-item">
                    <div class="cx-result-label">Decision</div>
                    <div style="margin-top: 6px;">{render_decision_badge(result["decision"])}</div>
                </div>
                """, unsafe_allow_html=True)

            # ── Confidence bars ──────────────────────────────────────────────
            st.markdown("")
            render_confidence_bars(result["domain_confidence"], result["risk_confidence"])

            # ── Reasoning ───────────────────────────────────────────────────
            st.markdown('<div class="cx-section-title">Reasoning</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="cx-card-compact">
                <div style="font-size: 13.5px; color: var(--text-primary); line-height: 1.65;">{_safe(result["reason"])}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Trigger keywords ─────────────────────────────────────────────
            if result.get("triggers"):
                st.markdown('<div class="cx-section-title">Detected Triggers</div>', unsafe_allow_html=True)
                render_trigger_tags(result["triggers"])

            # ── Detailed breakdown expander ──────────────────────────────────
            with st.expander("Detailed Analysis Breakdown"):
                render_explainability_panel(result)
                if result.get("retrieval_explanation"):
                    st.markdown(f"""
                    <div style="margin-top: 12px; font-size: 13px; color: var(--text-secondary); padding: 10px 14px;
                                background: var(--bg-secondary); border-radius: var(--radius-sm);
                                border-left: 3px solid var(--accent);">
                        <strong>Retrieval:</strong> {_safe(result["retrieval_explanation"])}
                    </div>
                    """, unsafe_allow_html=True)

            # ── Suggested Response ───────────────────────────────────────────
            st.markdown('<div class="cx-section-title">Suggested Response</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="cx-card" style="border-left: 3px solid var(--accent); border-radius: var(--radius-md);">
                <div style="font-size: 13.5px; line-height: 1.75; color: var(--text-primary); white-space: pre-wrap;">{_safe(result["response"])}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Retrieved Documents (premium cards) ──────────────────────────
            scored_docs = result.get("scored_docs", [])
            plain_docs  = result.get("docs", [])

            docs_to_show = scored_docs or plain_docs
            if docs_to_show:
                st.markdown('<div class="cx-section-title">Knowledge Base Sources</div>', unsafe_allow_html=True)
                for i, doc in enumerate(docs_to_show):
                    render_doc_snippet(doc, i)

            # ── Escalation Letter ────────────────────────────────────────────
            if letter_allowed:
                st.markdown("")
                st.markdown('<div class="cx-section-title">Escalation Letter</div>', unsafe_allow_html=True)

                if st.button("Generate Escalation Letter", type="primary", use_container_width=True):
                    with st.spinner("Generating letter..."):
                        letter = generate_letter(
                            ticket_text=result["ticket"],
                            domain=result["domain"],
                            risk=result["risk"],
                            decision=result["decision"],
                            triggers=result.get("triggers", []),
                            response=result.get("response", ""),
                            category=result.get("category", "GENERAL"),
                            use_ai=False,
                        )
                    st.session_state.last_letter = letter
                    st.session_state.last_letter_ticket_id = result.get("ticket_id")
                    _save_letter_once(result.get("ticket_id"), letter)

            if (st.session_state.get("last_letter") and
                    st.session_state.get("last_letter_ticket_id") == result.get("ticket_id")):
                letter = st.session_state.last_letter
                _render_letter_exports(letter)

        else:
            render_empty_state(
                "Enter a ticket to analyze",
                "Paste a customer support query on the left to get AI-powered classification, risk assessment, and response generation.",
            )


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: HISTORY
# ═══════════════════════════════════════════════════════════════════════════

elif page == "History":
    render_page_header("Ticket History", "Search, filter, and review previously analyzed tickets")

    history_df = get_history()

    if history_df.empty:
        render_empty_state("No tickets in history", "Analyzed tickets will appear here after processing.")
    else:
        # ── Filter bar ────────────────────────────────────────────────────────
        st.markdown("""
        <div style="padding: 14px 18px; background: var(--bg-card); border: 1px solid var(--border-color);
                    border-radius: var(--radius-md); margin-bottom: 16px; backdrop-filter: blur(14px);">
            <div style="font-size: 11px; font-weight: 700; color: var(--text-tertiary); text-transform: uppercase;
                        letter-spacing: 0.7px; margin-bottom: 10px;">Filter Tickets</div>
        </div>
        """, unsafe_allow_html=True)

        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        with f1:
            search_text = st.text_input("Search", placeholder="Search ticket content...", label_visibility="collapsed")
        with f2:
            domain_filter = st.selectbox("Domain", ["All Domains"] + list(history_df["domain"].unique()), label_visibility="collapsed")
        with f3:
            risk_filter = st.selectbox("Risk", ["All Risks"] + list(history_df["risk"].unique()), label_visibility="collapsed")
        with f4:
            decision_filter = st.selectbox("Decision", ["All Decisions"] + list(history_df["decision"].unique()), label_visibility="collapsed")

        filtered_df = history_df.copy()
        if domain_filter not in ("All", "All Domains"):
            filtered_df = filtered_df[filtered_df["domain"] == domain_filter]
        if risk_filter not in ("All", "All Risks"):
            filtered_df = filtered_df[filtered_df["risk"] == risk_filter]
        if decision_filter not in ("All", "All Decisions"):
            filtered_df = filtered_df[filtered_df["decision"] == decision_filter]
        if search_text:
            filtered_df = filtered_df[filtered_df["ticket_text"].str.contains(search_text, case=False, na=False)]

        # ── Results count ─────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center;
                    margin: 4px 0 14px 0;">
            <div style="font-size: 13px; color: var(--text-tertiary);">
                Showing <strong style="color: var(--text-primary);">{len(filtered_df)}</strong>
                of {len(history_df)} tickets
            </div>
        </div>
        """, unsafe_allow_html=True)

        for _, row in filtered_df.head(50).iterrows():
            render_ticket_card(row.to_dict())

        # ── Export ─────────────────────────────────────────────────────────────
        st.markdown("")
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Export Filtered Results as CSV",
            data=csv,
            file_name="cortexdesk_history.csv",
            mime="text/csv",
        )


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

elif page == "Analytics":
    render_page_header("Analytics", "Executive-level insights across your support operations")

    history_df = get_history()

    if history_df.empty:
        render_empty_state("No data yet", "Process some tickets to unlock analytics and trends.")
    else:
        total    = len(history_df)
        esc      = len(history_df[history_df["decision"] == "escalate"])
        resp_esc = len(history_df[history_df["decision"] == "respond_and_escalate"])
        auto_resp= len(history_df[history_df["decision"] == "respond"])

        # ── Top KPIs ─────────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card("Total Processed", total, "All-time tickets")
        with c2:
            render_metric_card("Auto-Responded", auto_resp, "AI handled directly", color="var(--risk-low)")
        with c3:
            render_metric_card("Respond & Escalate", resp_esc, "Dual-action decisions", color="var(--risk-high)")
        with c4:
            render_metric_card("Escalated", esc, "Immediate escalations", color="var(--risk-critical)")

        st.markdown("")

        # ── Risk distribution bar ─────────────────────────────────────────────
        st.markdown('<div class="cx-section-title">Risk Profile</div>', unsafe_allow_html=True)
        risk_counts = history_df["risk"].value_counts()
        render_risk_distribution_bar(
            low=int(risk_counts.get("low", 0)),
            medium=int(risk_counts.get("medium", 0)),
            high=int(risk_counts.get("high", 0)),
        )

        # ── Charts row ────────────────────────────────────────────────────────
        chart_left, chart_right = st.columns(2)

        with chart_left:
            st.markdown('<div class="cx-card-compact">', unsafe_allow_html=True)
            render_analytics_header("Tickets by Domain", "Volume distribution across support domains")
            domain_counts = history_df["domain"].value_counts().reset_index()
            domain_counts.columns = ["Domain", "Count"]
            st.bar_chart(domain_counts.set_index("Domain"), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_right:
            st.markdown('<div class="cx-card-compact">', unsafe_allow_html=True)
            render_analytics_header("Decision Breakdown", "How tickets were resolved")
            decision_counts = history_df["decision"].value_counts().reset_index()
            decision_counts.columns = ["Decision", "Count"]
            st.bar_chart(decision_counts.set_index("Decision"), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Volume over time ──────────────────────────────────────────────────
        if "timestamp" in history_df.columns:
            st.markdown('<div class="cx-card-compact">', unsafe_allow_html=True)
            render_analytics_header("Ticket Volume Over Time", "Daily ticket processing trend")
            try:
                history_df["date"] = pd.to_datetime(history_df["timestamp"]).dt.date
                daily_counts = history_df.groupby("date").size().reset_index(name="Tickets")
                daily_counts = daily_counts.set_index("date")
                st.line_chart(daily_counts, use_container_width=True)
            except Exception:
                st.info("Not enough time-series data to display trends.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── System performance ────────────────────────────────────────────────
        st.markdown('<div class="cx-section-title">System Performance</div>', unsafe_allow_html=True)
        call_stats = get_call_stats()
        from cache_manager import get_cache_stats
        cache_stats = get_cache_stats()

        p1, p2, p3, p4 = st.columns(4)
        with p1:
            render_metric_card("LLM Calls (session)", call_stats["total"])
        with p2:
            render_metric_card("Cache Hits", cache_stats["today"]["hits"])
        with p3:
            render_metric_card("Cache Hit Rate", f'{cache_stats["hit_rate"]:.0%}')
        with p4:
            render_metric_card("Tokens Saved", f'{cache_stats["today"]["tokens_saved"]:,}')


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: BULK UPLOAD
# ═══════════════════════════════════════════════════════════════════════════

elif page == "Bulk Upload":
    render_page_header("Bulk Upload", "Process multiple tickets simultaneously with the full AI triage pipeline")

    render_upload_zone_instructions()

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv", label_visibility="collapsed")

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            if "ticket_text" not in df.columns:
                st.error("CSV must contain a column named ticket_text.")
            else:
                st.markdown(f"""
                <div class="cx-card-compact" style="margin-top: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; font-weight: 700; color: var(--text-primary);">
                                {_safe(uploaded_file.name)}
                            </div>
                            <div style="font-size: 12.5px; color: var(--text-tertiary); margin-top: 3px;">
                                {len(df)} tickets ready for processing
                            </div>
                        </div>
                        <span class="cx-risk-badge cx-risk-low">Ready</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Start Processing", type="primary", use_container_width=True):
                    progress_bar = st.progress(0)
                    status_text  = st.empty()

                    results = []
                    total   = len(df)

                    for index, row in df.iterrows():
                        ticket_text = row["ticket_text"]
                        status_text.markdown(f"""
                        <div style="font-size: 13px; color: var(--text-secondary); padding: 8px 0;">
                            Processing ticket <strong style="color: var(--text-primary);">{index + 1}</strong>
                            of <strong style="color: var(--text-primary);">{total}</strong>...
                        </div>
                        """, unsafe_allow_html=True)
                        res = process_ticket(ticket_text)
                        results.append(res)
                        progress_bar.progress((index + 1) / total)

                    status_text.empty()

                    # Increment user stats
                    if st.session_state.current_user:
                        for _ in range(total):
                            increment_user_stat(st.session_state.current_user, "total_tickets_analyzed")

                    # ── Premium summary ──────────────────────────────────────
                    results_df = pd.DataFrame(results)
                    esc_count  = len(results_df[results_df["decision"] == "escalate"])
                    high_count = len(results_df[results_df["risk"] == "high"])
                    resp_count = len(results_df[results_df["decision"] == "respond"])
                    render_bulk_progress_summary(total, esc_count, high_count, resp_count)

                    # ── Results table ────────────────────────────────────────
                    st.markdown('<div class="cx-section-title">Processing Results</div>', unsafe_allow_html=True)
                    display_cols   = ["ticket", "domain", "risk", "decision"]
                    available_cols = [c for c in display_cols if c in results_df.columns]
                    st.dataframe(results_df[available_cols], use_container_width=True)

                    # ── Export ───────────────────────────────────────────────
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="Download Results as CSV",
                        data=csv,
                        file_name="bulk_processing_results.csv",
                        mime="text/csv",
                        type="primary",
                        use_container_width=True,
                    )

        except Exception:
            logger.exception("Error reading CSV")
            st.error("Unable to read the CSV file. Please verify the file format and try again.")

    else:
        st.markdown("""
        <div style="margin-top: 14px; padding: 16px 20px; background: var(--bg-card);
                    border: 1px solid var(--border-color); border-radius: var(--radius-md);">
            <div style="font-size: 13px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px;">
                CSV Format Requirements
            </div>
            <div style="font-size: 13px; color: var(--text-secondary); line-height: 1.7;">
                Your file must contain a column named ticket_text.
                Each row will be analyzed individually. You can optionally include additional
                metadata columns — they will be preserved in the export.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE: PROFILE
# ═══════════════════════════════════════════════════════════════════════════

elif page == "Profile":
    render_page_header("Profile", "Your account overview and activity statistics")

    username  = st.session_state.current_user or "User"
    user_data = get_user(username)

    if user_data:
        initials = username[0].upper()

        col_profile, col_stats = st.columns([1, 1.6])

        with col_profile:
            st.markdown(f"""
            <div class="cx-card" style="text-align: center; padding: 32px 24px;">
                <div class="cx-profile-avatar">{initials}</div>
                <div class="cx-profile-name">{_safe(user_data["username"])}</div>
                <div class="cx-profile-email">{_safe(user_data["email"])}</div>
                <div style="font-size: 12px; color: var(--text-tertiary); margin-top: 10px;
                            padding: 6px 14px; background: var(--accent-subtle);
                            border-radius: 999px; display: inline-block;
                            border: 1px solid rgba(45,212,191,0.15);">
                    Member since {_safe(user_data.get("created_at", "N/A"))}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_stats:
            st.markdown('<div class="cx-section-title">Activity Statistics</div>', unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            with m1:
                render_metric_card("Tickets Analyzed", user_data.get("total_tickets_analyzed", 0))
            with m2:
                render_metric_card("Escalations", user_data.get("total_escalations", 0), color="var(--risk-medium)")
            with m3:
                render_metric_card("Letters Generated", user_data.get("total_letters_generated", 0), color="var(--accent)")

        # ── Generated Letters History ─────────────────────────────────────────
        st.markdown("")
        st.markdown('<div class="cx-section-title">Escalation Letters</div>', unsafe_allow_html=True)

        letters_df = get_user_letters(generated_by=username)
        if letters_df.empty:
            render_empty_state(
                "No letters generated yet",
                "Generate escalation letters from the Analyze Ticket page."
            )
        else:
            for _, row in letters_df.head(10).iterrows():
                sev   = row.get("severity", "N/A")
                subj  = row.get("subject", "Letter")
                ts    = row.get("timestamp", "")
                with st.expander(f"{sev} — {subj} ({ts})"):
                    st.markdown(f"""
                    <div class="cx-letter-preview" style="font-size: 13px;">
                        {_safe(row.get('body', '')).replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)

        # ── Recent ticket activity ────────────────────────────────────────────
        st.markdown('<div class="cx-section-title">Recent Ticket Activity</div>', unsafe_allow_html=True)
        history_df = get_history()
        if not history_df.empty:
            for _, row in history_df.head(5).iterrows():
                render_ticket_card(row.to_dict())
        else:
            render_empty_state("No recent activity", "Your analyzed tickets will appear here.")

    else:
        render_empty_state("Profile not found", "Please sign out and sign in again.")
