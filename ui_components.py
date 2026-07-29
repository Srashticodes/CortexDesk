"""
ui_components.py — Premium design system and component library for CortexDesk AI.

Provides consistent, enterprise-grade UI components rendered via
Streamlit's st.markdown(unsafe_allow_html=True). Inspired by
Linear, Stripe Dashboard, Vercel, and Datadog aesthetics.
"""

import html
import streamlit as st


# ---------------------------------------------------------------------------
# Design System — Global CSS
# ---------------------------------------------------------------------------
def inject_global_css(dark_mode: bool = False):
    """Inject the complete design system CSS into the Streamlit app."""
    theme_class = "cx-theme-dark" if dark_mode else "cx-theme-light"
    if not dark_mode:
        theme_overrides = """
        color-scheme: light;
        --bg-primary: #f0f6fa;
        --bg-secondary: #e2edf5;
        --bg-card: rgba(255, 255, 255, 0.96);
        --bg-elevated: #ffffff;
        --bg-input: rgba(255,255,255,0.9);
        --border-color: rgba(14, 116, 144, 0.16);
        --border-subtle: rgba(71, 85, 105, 0.10);
        --text-primary: #0a1929;
        --text-secondary: #334e68;
        --text-tertiary: #627d98;
        --accent-subtle: rgba(20, 184, 166, 0.10);
        --shadow-sm: 0 4px 16px rgba(15, 23, 42, 0.06);
        --shadow-md: 0 12px 36px rgba(15, 23, 42, 0.10), 0 0 0 1px rgba(14,116,144,0.05);
        --shadow-lg: 0 20px 60px rgba(15, 23, 42, 0.13);
        --sidebar-bg: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 55%, #e2e8f0 100%);
        --sidebar-border: rgba(14, 116, 144, 0.14);
        background:
            radial-gradient(ellipse at 12% 0%, rgba(45, 212, 191, 0.15) 0%, transparent 40%),
            radial-gradient(ellipse at 90% 10%, rgba(56, 189, 248, 0.10) 0%, transparent 35%),
            linear-gradient(160deg, #f0f6fa 0%, #e8f4f9 100%) !important;
        color: #0a1929 !important;
        """
        root_vars = """
        --bg-primary:    #f0f6fa;
        --bg-secondary:  #e2edf5;
        --bg-card:       rgba(255, 255, 255, 0.96);
        --bg-elevated:   #ffffff;
        --bg-input:      rgba(255,255,255,0.9);
        --border-color:  rgba(14, 116, 144, 0.16);
        --border-subtle: rgba(71, 85, 105, 0.10);
        --text-primary:  #0a1929;
        --text-secondary:#334e68;
        --text-tertiary: #627d98;
        --text-inverse:  #ffffff;
        --accent:        #0d9488;
        --accent-hover:  #0f766e;
        --accent-strong: #0284c7;
        --accent-warm:   #ea580c;
        --accent-subtle: rgba(20, 184, 166, 0.10);
        --risk-critical: #e11d48;
        --risk-critical-bg: rgba(225, 29, 72, 0.10);
        --risk-high:     #ea580c;
        --risk-high-bg:  rgba(234, 88, 12, 0.10);
        --risk-medium:   #ca8a04;
        --risk-medium-bg:rgba(202, 138, 4, 0.10);
        --risk-low:      #059669;
        --risk-low-bg:   rgba(5, 150, 105, 0.10);
        --shadow-sm:     0 4px 16px rgba(15, 23, 42, 0.06);
        --shadow-md:     0 12px 36px rgba(15, 23, 42, 0.10), 0 0 0 1px rgba(14,116,144,0.05);
        --shadow-lg:     0 20px 60px rgba(15, 23, 42, 0.13);
        --radius-sm:     6px;
        --radius-md:     10px;
        --radius-lg:     14px;
        --radius-xl:     18px;
        --transition:    all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        --sidebar-bg:    linear-gradient(180deg, #f8fafc 0%, #f1f5f9 55%, #e2e8f0 100%);
        --sidebar-border:rgba(14, 116, 144, 0.14);
        """
    else:
        theme_overrides = """
        color-scheme: dark;
        --bg-primary: #07111f;
        --bg-secondary: #0d1b2e;
        --bg-card: rgba(13, 24, 41, 0.90);
        --bg-elevated: rgba(18, 32, 54, 0.96);
        --bg-input: rgba(10, 20, 35, 0.85);
        --border-color: rgba(125, 211, 252, 0.14);
        --border-subtle: rgba(148, 163, 184, 0.08);
        --text-primary: #eef6ff;
        --text-secondary: #b8c7d9;
        --text-tertiary: #7d90a8;
        --accent-subtle: rgba(45, 212, 191, 0.11);
        --shadow-sm: 0 4px 20px rgba(0,0,0,0.20);
        --shadow-md: 0 12px 44px rgba(0,0,0,0.28), 0 0 0 1px rgba(45,212,191,0.05);
        --shadow-lg: 0 24px 80px rgba(0,0,0,0.38), 0 0 40px rgba(56,189,248,0.08);
        --sidebar-bg: linear-gradient(180deg, #060f1c 0%, #0a1929 55%, #060f1c 100%);
        --sidebar-border: rgba(45, 212, 191, 0.12);
        background:
            radial-gradient(ellipse at 12% 0%, rgba(45, 212, 191, 0.13) 0%, transparent 40%),
            radial-gradient(ellipse at 90% 10%, rgba(56, 189, 248, 0.09) 0%, transparent 35%),
            radial-gradient(ellipse at 55% 95%, rgba(249, 115, 22, 0.07) 0%, transparent 35%),
            linear-gradient(160deg, #07111f 0%, #0d1b2e 100%) !important;
        color: #eef6ff !important;
        """
        root_vars = """
        --bg-primary:    #07111f;
        --bg-secondary:  #0d1b2e;
        --bg-card:       rgba(13, 24, 41, 0.90);
        --bg-elevated:   rgba(18, 32, 54, 0.96);
        --bg-input:      rgba(10, 20, 35, 0.85);
        --border-color:  rgba(125, 211, 252, 0.14);
        --border-subtle: rgba(148, 163, 184, 0.08);
        --text-primary:  #eef6ff;
        --text-secondary:#b8c7d9;
        --text-tertiary: #7d90a8;
        --text-inverse:  #ffffff;
        --accent:        #2dd4bf;
        --accent-hover:  #14b8a6;
        --accent-strong: #38bdf8;
        --accent-warm:   #f97316;
        --accent-subtle: rgba(45, 212, 191, 0.11);
        --risk-critical: #ff4d6d;
        --risk-critical-bg: rgba(255, 77, 109, 0.12);
        --risk-high:     #fb923c;
        --risk-high-bg:  rgba(251, 146, 60, 0.12);
        --risk-medium:   #facc15;
        --risk-medium-bg:rgba(250, 204, 21, 0.12);
        --risk-low:      #34d399;
        --risk-low-bg:   rgba(52, 211, 153, 0.12);
        --shadow-sm:     0 4px 20px rgba(0,0,0,0.20);
        --shadow-md:     0 12px 44px rgba(0,0,0,0.28), 0 0 0 1px rgba(45,212,191,0.05);
        --shadow-lg:     0 24px 80px rgba(0,0,0,0.38), 0 0 40px rgba(56,189,248,0.08);
        --radius-sm:     6px;
        --radius-md:     10px;
        --radius-lg:     14px;
        --radius-xl:     18px;
        --transition:    all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        --sidebar-bg:    linear-gradient(180deg, #060f1c 0%, #0a1929 55%, #060f1c 100%);
        --sidebar-border:rgba(45, 212, 191, 0.12);
        """


    css = """
    <style>
    /* ===== Google Fonts ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ===== Keyframe Animations ===== */
    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }

    @keyframes shimmer {
        0%   { background-position: -200% center; }
        100% { background-position: 200% center; }
    }

    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(45, 212, 191, 0); }
        50%       { box-shadow: 0 0 0 8px rgba(45, 212, 191, 0.12); }
    }

    @keyframes pulseRing {
        0%   { transform: scale(1); opacity: 0.6; }
        100% { transform: scale(1.55); opacity: 0; }
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    @keyframes progressShimmer {
        0%   { background-position: -200px 0; }
        100% { background-position: calc(200px + 100%) 0; }
    }

    @keyframes dotBlink {
        0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
        40%           { opacity: 1;   transform: scale(1); }
    }

    /* ===== CSS Custom Properties ===== */
    :root {
        __ROOT_VARS__
    }


    /* ===== Base ===== */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        min-height: 100vh;
    }

    /* ===== Per-run theme overrides — injected fresh on every Streamlit re-run ===== */
    .stApp { __THEME_OVERRIDES__ }


    /* ===== Scrollbar ===== */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(45, 212, 191, 0.28);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(45, 212, 191, 0.50);
    }

    /* ===== Hide Streamlit chrome ===== */
    header[data-testid="stHeader"] {
        background: transparent !important;
        backdrop-filter: none !important;
    }
    #MainMenu, footer { visibility: hidden !important; }

    /* ===== Transparent iframes for components.html (e.g. Spline viewer) ===== */
    iframe[title="stCustomComponentV1"] {
        background: transparent !important;
        border: none !important;
    }

    .block-container {
        max-width: 1340px !important;
        padding-top: 24px !important;
        padding-bottom: 72px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    div[data-testid="stVerticalBlock"] { gap: 0.75rem; }

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--sidebar-border) !important;
        box-shadow: 20px 0 60px rgba(0, 0, 0, 0.22);
        backdrop-filter: blur(24px) saturate(160%);
    }

    section[data-testid="stSidebar"] * {
        color: var(--text-secondary) !important;
    }

    /* Sidebar nav items */
    section[data-testid="stSidebar"] .stRadio label {
        padding: 10px 14px !important;
        border-radius: 9px !important;
        transition: var(--transition) !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
        margin: 2px 0 !important;
        border: 1px solid transparent !important;
        letter-spacing: -0.1px;
        display: flex !important;
        align-items: center !important;
        gap: 8px;
    }

    section[data-testid="stSidebar"] .stRadio label:hover {
        background: var(--accent-subtle) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-color) !important;
    }

    section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[aria-checked="true"] {
        background: var(--accent-subtle) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-color) !important;
        font-weight: 700 !important;
        box-shadow: var(--shadow-sm) !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: rgba(45, 212, 191, 0.08) !important;
        margin: 12px 0 !important;
    }

    section[data-testid="stSidebar"] .stButton button {
        background: transparent !important;
        border: 1px solid rgba(45, 212, 191, 0.16) !important;
        color: #7d90a8 !important;
        font-size: 12.5px !important;
        border-radius: var(--radius-sm) !important;
        transition: var(--transition) !important;
        font-weight: 500 !important;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(45, 212, 191, 0.08) !important;
        border-color: rgba(45, 212, 191, 0.28) !important;
        color: #2dd4bf !important;
    }

    section[data-testid="stSidebar"] .stToggle {
        margin: 4px 0 !important;
    }

    /* ===== CARDS ===== */
    .cx-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 24px;
        box-shadow: var(--shadow-sm);
        backdrop-filter: blur(18px) saturate(140%);
        transition: var(--transition);
        margin-bottom: 16px;
        animation: fadeSlideUp 0.38s ease both;
    }
    .cx-card:hover {
        box-shadow: var(--shadow-md);
        border-color: rgba(45, 212, 191, 0.22);
    }

    .cx-card-compact {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        box-shadow: var(--shadow-sm);
        margin-bottom: 12px;
        backdrop-filter: blur(14px);
        animation: fadeSlideUp 0.38s ease both;
    }

    .cx-panel {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 20px;
        box-shadow: var(--shadow-sm);
        backdrop-filter: blur(18px);
    }

    /* ===== METRIC CARDS ===== */
    .cx-metric {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 22px 24px;
        box-shadow: var(--shadow-sm);
        backdrop-filter: blur(16px) saturate(140%);
        transition: var(--transition);
        position: relative;
        overflow: hidden;
        animation: fadeSlideUp 0.4s ease both;
    }

    .cx-metric::before {
        content: "";
        position: absolute;
        inset: 0 0 auto 0;
        height: 2px;
        background: linear-gradient(90deg, var(--accent), var(--accent-strong), transparent 80%);
        opacity: 0.9;
    }

    .cx-metric::after {
        content: "";
        position: absolute;
        bottom: -30px;
        right: -20px;
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(45,212,191,0.06), transparent 70%);
        pointer-events: none;
    }

    .cx-metric:hover {
        box-shadow: var(--shadow-md);
        border-color: rgba(45, 212, 191, 0.22);
        transform: translateY(-1px);
    }

    .cx-metric-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        color: var(--text-tertiary);
        margin-bottom: 10px;
    }

    .cx-metric-value {
        font-size: 30px;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1.1;
        letter-spacing: -1px;
    }

    .cx-metric-subtitle {
        font-size: 12px;
        color: var(--text-tertiary);
        margin-top: 5px;
    }

    /* ===== RISK BADGES ===== */
    .cx-risk-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.2px;
        white-space: nowrap;
    }
    .cx-risk-high {
        background: var(--risk-critical-bg);
        color: var(--risk-critical);
        border: 1px solid rgba(255, 77, 109, 0.25);
    }
    .cx-risk-medium {
        background: var(--risk-medium-bg);
        color: var(--risk-medium);
        border: 1px solid rgba(250, 204, 21, 0.25);
    }
    .cx-risk-low {
        background: var(--risk-low-bg);
        color: var(--risk-low);
        border: 1px solid rgba(52, 211, 153, 0.25);
    }

    .cx-risk-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        display: inline-block;
        flex-shrink: 0;
    }
    .cx-risk-dot-high   { background: var(--risk-critical); box-shadow: 0 0 5px rgba(255,77,109,0.6); }
    .cx-risk-dot-medium { background: var(--risk-medium);   box-shadow: 0 0 5px rgba(250,204,21,0.5); }
    .cx-risk-dot-low    { background: var(--risk-low);      box-shadow: 0 0 5px rgba(52,211,153,0.5); }

    /* ===== DECISION BADGES ===== */
    .cx-decision-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        white-space: nowrap;
    }
    .cx-decision-escalate {
        background: var(--risk-critical-bg);
        color: var(--risk-critical);
        border: 1px solid rgba(255, 77, 109, 0.25);
    }
    .cx-decision-respond_and_escalate {
        background: var(--risk-high-bg);
        color: var(--risk-high);
        border: 1px solid rgba(251, 146, 60, 0.25);
    }
    .cx-decision-respond {
        background: var(--risk-low-bg);
        color: var(--risk-low);
        border: 1px solid rgba(52, 211, 153, 0.25);
    }

    /* ===== CONFIDENCE BARS ===== */
    .cx-confidence-container { margin: 10px 0; }
    .cx-confidence-label {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 6px;
    }
    .cx-confidence-track {
        height: 7px;
        background: rgba(255,255,255,0.05);
        border-radius: 4px;
        overflow: hidden;
    }
    .cx-confidence-fill {
        height: 100%;
        border-radius: 4px;
        background: linear-gradient(90deg, var(--accent), var(--accent-strong));
        background-size: 200px 100%;
        animation: progressShimmer 2.2s linear infinite, fadeIn 0.5s ease;
    }

    /* ===== PAGE HEADERS ===== */
    .cx-page-header {
        position: relative;
        margin-bottom: 28px;
        padding: 28px 32px;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-xl);
        background:
            linear-gradient(135deg, rgba(45, 212, 191, 0.10) 0%, transparent 50%),
            var(--bg-card);
        box-shadow: var(--shadow-md);
        overflow: hidden;
        animation: fadeSlideUp 0.35s ease both;
    }

    .cx-page-header::before {
        content: "";
        position: absolute;
        inset: 0 0 auto 0;
        height: 2px;
        background: linear-gradient(90deg, var(--accent), var(--accent-strong), transparent 70%);
    }

    .cx-page-header::after {
        content: "";
        position: absolute;
        right: -80px;
        top: -80px;
        width: 280px;
        height: 280px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(56,189,248,0.12) 0%, transparent 65%);
        pointer-events: none;
    }

    .cx-page-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 12px;
        padding: 4px 12px;
        border-radius: 999px;
        background: var(--accent-subtle);
        border: 1px solid rgba(45, 212, 191, 0.20);
        color: var(--accent);
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .cx-page-eyebrow::before {
        content: "";
        display: inline-block;
        width: 5px; height: 5px;
        border-radius: 50%;
        background: var(--accent);
        box-shadow: 0 0 6px rgba(45,212,191,0.7);
        animation: pulseGlow 2.5s ease-in-out infinite;
    }

    .cx-page-title {
        font-size: 32px;
        font-weight: 800;
        color: var(--text-primary);
        margin: 0 0 8px 0;
        letter-spacing: -1px;
        line-height: 1.1;
    }

    .cx-page-subtitle {
        font-size: 14.5px;
        color: var(--text-tertiary);
        margin: 0;
        line-height: 1.6;
        max-width: 700px;
    }

    /* ===== SECTION TITLES ===== */
    .cx-section-title {
        font-size: 13px;
        font-weight: 700;
        color: var(--text-secondary);
        margin: 22px 0 10px 0;
        letter-spacing: 0.3px;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .cx-section-title::before {
        content: "";
        display: inline-block;
        width: 3px; height: 14px;
        border-radius: 2px;
        background: linear-gradient(180deg, var(--accent), var(--accent-strong));
        flex-shrink: 0;
    }

    /* ===== TICKET CARDS ===== */
    .cx-ticket-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        margin-bottom: 8px;
        transition: var(--transition);
        cursor: default;
        animation: fadeSlideUp 0.35s ease both;
    }
    .cx-ticket-card:hover {
        border-color: rgba(45, 212, 191, 0.22);
        box-shadow: var(--shadow-sm);
        transform: translateY(-1px);
    }
    .cx-ticket-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .cx-ticket-domain {
        font-size: 11px;
        font-weight: 700;
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 0.7px;
        padding: 2px 8px;
        background: var(--accent-subtle);
        border-radius: 999px;
        border: 1px solid rgba(45,212,191,0.15);
    }
    .cx-ticket-time {
        font-size: 11.5px;
        color: var(--text-tertiary);
    }
    .cx-ticket-text {
        font-size: 13.5px;
        color: var(--text-primary);
        line-height: 1.55;
        margin-bottom: 10px;
    }
    .cx-ticket-meta {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
    }

    /* ===== DOC SNIPPET CARDS (Premium) ===== */
    .cx-doc-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 0;
        margin-bottom: 10px;
        overflow: hidden;
        transition: var(--transition);
        animation: fadeSlideUp 0.38s ease both;
    }
    .cx-doc-card:hover {
        box-shadow: var(--shadow-sm);
        border-color: rgba(45, 212, 191, 0.22);
    }
    .cx-doc-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 14px;
        border-bottom: 1px solid var(--border-subtle);
        gap: 10px;
    }
    .cx-doc-card-left {
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
        min-width: 0;
    }
    .cx-doc-card-icon {
        width: 28px; height: 28px;
        border-radius: 7px;
        background: var(--accent-subtle);
        border: 1px solid rgba(45,212,191,0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        flex-shrink: 0;
        color: var(--accent);
        font-weight: 700;
    }
    .cx-doc-card-source {
        font-size: 12px;
        font-weight: 700;
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .cx-doc-card-right {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-shrink: 0;
    }
    .cx-doc-score-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 11.5px;
        font-weight: 700;
        white-space: nowrap;
    }
    .cx-doc-score-high {
        background: var(--risk-low-bg);
        color: var(--risk-low);
        border: 1px solid rgba(52,211,153,0.22);
    }
    .cx-doc-score-medium {
        background: var(--risk-medium-bg);
        color: var(--risk-medium);
        border: 1px solid rgba(250,204,21,0.22);
    }
    .cx-doc-score-low {
        background: rgba(148,163,184,0.10);
        color: var(--text-tertiary);
        border: 1px solid rgba(148,163,184,0.15);
    }
    .cx-doc-relevance-bar {
        height: 3px;
        border-radius: 0;
    }
    .cx-doc-card-body {
        padding: 12px 14px;
        font-size: 13px;
        color: var(--text-secondary);
        line-height: 1.65;
    }
    .cx-doc-index-chip {
        font-size: 11px;
        color: var(--text-tertiary);
        padding: 2px 7px;
        border-radius: 999px;
        border: 1px solid var(--border-subtle);
        background: transparent;
        white-space: nowrap;
    }

    /* Legacy doc snippet (keep for backward compat) */
    .cx-doc-snippet {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-sm);
        padding: 12px 16px;
        font-size: 13px;
        color: var(--text-secondary);
        line-height: 1.6;
        margin-bottom: 8px;
    }
    .cx-doc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .cx-doc-source { font-size: 11px; font-weight: 600; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; }
    .cx-doc-score  { font-size: 11px; font-weight: 500; color: var(--text-tertiary); background: var(--bg-elevated); padding: 2px 8px; border-radius: 10px; border: 1px solid var(--border-color); }

    /* ===== EMPTY STATES ===== */
    .cx-empty-state {
        text-align: center;
        padding: 56px 24px;
        color: var(--text-tertiary);
        animation: fadeIn 0.5s ease;
    }
    .cx-empty-icon-svg {
        margin: 0 auto 20px auto;
        width: 56px; height: 56px;
        opacity: 0.35;
    }
    .cx-empty-title {
        font-size: 17px;
        font-weight: 700;
        color: var(--text-secondary);
        margin-bottom: 6px;
    }
    .cx-empty-text {
        font-size: 14px;
        color: var(--text-tertiary);
        max-width: 380px;
        margin: 0 auto;
        line-height: 1.6;
    }
    /* keep legacy class for backward-compat */
    .cx-empty-icon { font-size: 32px; margin-bottom: 14px; opacity: 0.3; }

    /* ===== STATUS DOTS ===== */
    .cx-status-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .cx-status-online  { background: #22c55e; box-shadow: 0 0 7px rgba(34,197,94,0.55); }
    .cx-status-offline { background: #ef4444; }
    .cx-status-warning { background: #f59e0b; box-shadow: 0 0 7px rgba(245,158,11,0.5); }

    /* ===== TRIGGER TAGS ===== */
    .cx-trigger-tag {
        display: inline-block;
        padding: 3px 10px;
        background: rgba(249, 115, 22, 0.10);
        color: #fb923c;
        border-radius: 999px;
        font-size: 11.5px;
        font-weight: 600;
        margin: 3px 4px 3px 0;
        border: 1px solid rgba(249, 115, 22, 0.20);
        letter-spacing: 0.2px;
    }

    /* ===== EXPLAINABILITY PANEL ===== */
    .cx-explain-panel {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        margin: 12px 0;
    }
    .cx-explain-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 8px 0;
        border-bottom: 1px solid var(--border-subtle);
        font-size: 13px;
    }
    .cx-explain-item:last-child { border-bottom: none; }
    .cx-explain-key {
        font-weight: 600;
        color: var(--text-secondary);
        min-width: 140px;
        flex-shrink: 0;
    }
    .cx-explain-value { color: var(--text-primary); }

    /* ===== LETTER PREVIEW ===== */
    .cx-letter-preview {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 28px 36px;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        line-height: 1.75;
        color: var(--text-primary);
        white-space: pre-wrap;
        box-shadow: var(--shadow-md);
    }
    .cx-letter-subject {
        font-size: 18px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 18px;
        padding-bottom: 14px;
        border-bottom: 2px solid var(--accent);
    }

    /* ===== ACTIVITY FEED ===== */
    .cx-activity-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 10px 0;
        border-bottom: 1px solid var(--border-subtle);
    }
    .cx-activity-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        margin-top: 5px;
        flex-shrink: 0;
    }
    .cx-activity-content { flex: 1; min-width: 0; }
    .cx-activity-text { font-size: 13px; color: var(--text-primary); line-height: 1.4; }
    .cx-activity-time { font-size: 11px; color: var(--text-tertiary); margin-top: 3px; }

    /* ===== AUTH PAGE ===== */
    .cx-auth-split {
        display: flex;
        min-height: 100vh;
        animation: fadeIn 0.5s ease;
    }
    .cx-auth-left {
        flex: 1;
        background:
            radial-gradient(ellipse at 30% 30%, rgba(45,212,191,0.22) 0%, transparent 55%),
            radial-gradient(ellipse at 75% 70%, rgba(56,189,248,0.15) 0%, transparent 50%),
            linear-gradient(145deg, #060e1b, #0d1b2e);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 48px;
        position: relative;
        overflow: hidden;
    }
    .cx-auth-logo-mark {
        width: 48px; height: 48px;
        background: linear-gradient(135deg, #2dd4bf, #38bdf8);
        border-radius: var(--radius-md);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: #07111f;
        font-weight: 800;
        font-size: 22px;
        margin-bottom: 16px;
        box-shadow: 0 0 0 0 rgba(45,212,191,0);
        animation: pulseGlow 3s ease-in-out infinite;
    }
    .cx-auth-title  { font-size: 22px; font-weight: 800; color: var(--text-primary); margin: 0; letter-spacing: -0.5px; }
    .cx-auth-subtitle { font-size: 13.5px; color: var(--text-tertiary); margin-top: 4px; }

    /* ===== PROFILE ===== */
    .cx-profile-avatar {
        width: 76px; height: 76px;
        background: linear-gradient(135deg, #2dd4bf, #38bdf8);
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: #07111f;
        font-weight: 800;
        font-size: 30px;
        margin-bottom: 14px;
        box-shadow: 0 0 0 4px rgba(45,212,191,0.15), 0 0 0 8px rgba(45,212,191,0.06);
    }
    .cx-profile-name  { font-size: 20px; font-weight: 700; color: var(--text-primary); }
    .cx-profile-email { font-size: 13.5px; color: var(--text-tertiary); margin-top: 3px; }

    /* ===== UPLOAD ZONE ===== */
    .cx-upload-zone {
        border: 2px dashed var(--border-color);
        border-radius: var(--radius-lg);
        padding: 52px 32px;
        text-align: center;
        background: rgba(45,212,191,0.02);
        transition: var(--transition);
        cursor: pointer;
        position: relative;
    }
    .cx-upload-zone:hover {
        border-color: var(--accent);
        background: var(--accent-subtle);
    }
    .cx-upload-icon {
        font-size: 36px;
        margin-bottom: 14px;
        opacity: 0.5;
        display: block;
    }
    .cx-upload-title {
        font-size: 16px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 6px;
    }
    .cx-upload-subtitle {
        font-size: 13px;
        color: var(--text-tertiary);
        line-height: 1.6;
    }

    /* ===== ANALYTICS CHART CARDS ===== */
    .cx-chart-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 0;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
        backdrop-filter: blur(14px);
        animation: fadeSlideUp 0.4s ease both;
        margin-bottom: 16px;
    }
    .cx-chart-card-header {
        padding: 16px 20px 14px;
        border-bottom: 1px solid var(--border-subtle);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .cx-chart-card-title {
        font-size: 13.5px;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.2px;
    }
    .cx-chart-card-subtitle {
        font-size: 12px;
        color: var(--text-tertiary);
        margin-top: 2px;
    }
    .cx-chart-card-body {
        padding: 14px 16px 4px;
    }

    /* ===== COMMAND/STATUS BAR ===== */
    .cx-command-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        padding: 11px 16px;
        margin-bottom: 20px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        backdrop-filter: blur(14px);
        animation: fadeIn 0.4s ease;
    }
    .cx-command-left  { display: flex; align-items: center; gap: 10px; min-width: 0; }
    .cx-command-mark  {
        width: 30px; height: 30px;
        border-radius: 8px;
        background: linear-gradient(135deg, var(--accent), var(--accent-strong));
        display: flex; align-items: center; justify-content: center;
        color: #07111f; font-weight: 800; flex-shrink: 0; font-size: 13px;
    }
    .cx-command-title { font-size: 14px; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
    .cx-command-meta  { font-size: 11.5px; color: var(--text-tertiary); line-height: 1.2; margin-top: 2px; }
    .cx-command-status { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }

    .cx-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 10px;
        border: 1px solid var(--border-color);
        background: var(--bg-elevated);
        border-radius: 999px;
        color: var(--text-secondary);
        font-size: 11.5px;
        font-weight: 600;
        white-space: nowrap;
    }

    /* ===== RESULT ITEMS ===== */
    .cx-result-item {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        animation: fadeSlideUp 0.36s ease both;
    }
    .cx-result-label {
        font-size: 10.5px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        color: var(--text-tertiary);
        margin-bottom: 8px;
    }
    .cx-result-value {
        font-size: 15px;
        font-weight: 700;
        color: var(--text-primary);
    }

    /* ===== INSIGHT GRID ===== */
    .cx-insight-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 16px;
    }
    .cx-insight {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 14px 16px;
        box-shadow: var(--shadow-sm);
        animation: fadeSlideUp 0.38s ease both;
    }
    .cx-insight-label { color: var(--text-tertiary); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .cx-insight-value { color: var(--text-primary); font-size: 22px; font-weight: 800; line-height: 1.1; letter-spacing: -0.5px; }
    .cx-insight-note  { color: var(--text-tertiary); font-size: 12px; margin-top: 6px; line-height: 1.4; }

    /* ===== WORKFLOW STEPS ===== */
    .cx-workflow {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        margin: 12px 0 18px 0;
    }
    .cx-workflow-step {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 14px;
        animation: fadeSlideUp 0.38s ease both;
    }
    .cx-step-index {
        width: 24px; height: 24px;
        border-radius: 7px;
        display: inline-flex;
        align-items: center; justify-content: center;
        background: var(--accent-subtle);
        color: var(--accent);
        font-size: 12px; font-weight: 800;
        margin-bottom: 10px;
    }
    .cx-step-title { color: var(--text-primary); font-size: 13px; font-weight: 700; margin-bottom: 4px; }
    .cx-step-text  { color: var(--text-tertiary); font-size: 12px; line-height: 1.45; }

    /* ===== FORMS ===== */
    .stTextInput input, .stTextArea textarea {
        border: 1px solid var(--border-color) !important;
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        transition: var(--transition) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(45,212,191,0.13) !important;
        outline: none !important;
    }

    div[data-testid="stForm"] {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 22px;
        box-shadow: var(--shadow-sm);
        backdrop-filter: blur(14px);
        animation: fadeSlideUp 0.38s ease both;
    }

    /* Primary buttons */
    .stButton button[kind="primary"],
    .stFormSubmitButton button {
        background: linear-gradient(135deg, var(--accent), var(--accent-strong)) !important;
        color: #07111f !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 9px 22px !important;
        transition: var(--transition) !important;
        letter-spacing: -0.2px;
        box-shadow: 0 4px 16px rgba(45,212,191,0.22) !important;
    }
    .stButton button[kind="primary"]:hover,
    .stFormSubmitButton button:hover {
        background: linear-gradient(135deg, var(--accent-hover), var(--accent)) !important;
        box-shadow: 0 6px 22px rgba(45,212,191,0.32) !important;
        transform: translateY(-1px);
    }

    /* Secondary/download buttons */
    .stDownloadButton button, .stButton button:not([kind="primary"]) {
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        transition: var(--transition) !important;
        font-size: 13.5px !important;
    }
    .stDownloadButton button:hover, .stButton button:not([kind="primary"]):hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: var(--accent-subtle) !important;
    }

    /* Toggles & checkboxes */
    .stToggle label, .stCheckbox label {
        color: var(--text-secondary) !important;
        font-size: 13.5px !important;
    }

    .stMarkdown, .stMarkdown p, label, [data-testid="stWidgetLabel"],
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        color: var(--text-primary);
    }

    /* Selects */
    div[data-baseweb="select"] > div,
    div[data-baseweb="popover"] ul {
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-color) !important;
        border-radius: var(--radius-sm) !important;
    }
    div[data-baseweb="select"] span,
    div[data-baseweb="popover"] li { color: var(--text-primary) !important; }

    /* Alerts */
    div[data-testid="stAlert"] { color: var(--text-primary) !important; border-radius: var(--radius-md) !important; }

    /* ===== PROGRESS BARS ===== */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--accent), var(--accent-strong)) !important;
        border-radius: 4px !important;
        background-size: 200px 100% !important;
        animation: progressShimmer 1.8s linear infinite !important;
    }
    .stProgress > div {
        background: rgba(255,255,255,0.06) !important;
        border-radius: 4px !important;
        height: 8px !important;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px !important;
        border-bottom: 1px solid var(--border-color) !important;
        background: transparent !important;
        padding-bottom: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        padding: 9px 18px !important;
        color: var(--text-tertiary) !important;
        border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
        border: 1px solid transparent !important;
        border-bottom: none !important;
        transition: var(--transition) !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
        background: var(--accent-subtle) !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--accent) !important;
        border-color: var(--border-color) !important;
        border-bottom-color: var(--bg-primary) !important;
        background: var(--bg-card) !important;
    }

    /* ===== DATAFRAME ===== */
    .stDataFrame {
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-md) !important;
        overflow: hidden;
    }

    /* ===== NATIVE METRIC ===== */
    [data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 14px 16px;
    }

    /* ===== EXPANDERS ===== */
    .streamlit-expanderHeader {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        color: var(--text-primary) !important;
        border-radius: var(--radius-sm) !important;
        padding: 10px 14px !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
    }
    .streamlit-expanderContent {
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius-sm) var(--radius-sm) !important;
        background: var(--bg-secondary) !important;
    }

    /* ===== FILE UPLOADER ===== */
    [data-testid="stFileUploaderDropzone"] {
        border: 2px dashed var(--border-color) !important;
        border-radius: var(--radius-lg) !important;
        background: rgba(45,212,191,0.02) !important;
        padding: 32px !important;
        transition: var(--transition) !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: var(--accent) !important;
        background: var(--accent-subtle) !important;
    }

    /* ===== SELECTBOX ===== */
    .stSelectbox > div > div { border-radius: var(--radius-sm) !important; }

    /* ===== HIDE DATAFRAME INDEX ===== */
    .row_heading.level0 { display: none; }
    .blank { display: none; }

    /* ===== SPINNER ===== */
    [data-testid="stSpinner"] > div {
        border-top-color: var(--accent) !important;
        border-right-color: rgba(45,212,191,0.25) !important;
        border-bottom-color: rgba(45,212,191,0.25) !important;
        border-left-color: rgba(45,212,191,0.25) !important;
    }

    /* ===== RESPONSIVE ===== */
    @media (max-width: 900px) {
        .block-container { padding-left: 16px !important; padding-right: 16px !important; }
        .cx-page-title { font-size: 24px !important; }
        .cx-insight-grid, .cx-workflow { grid-template-columns: 1fr 1fr; }
        .cx-command-bar { flex-direction: column; align-items: flex-start; }
    }
    @media (max-width: 600px) {
        .cx-insight-grid, .cx-workflow { grid-template-columns: 1fr; }
    }

    </style>
    <script>
    (function() {
        document.body.classList.remove("cx-theme-dark", "cx-theme-light");
        document.body.classList.add("__THEME_CLASS__");
        // Also force Streamlit's own root element to adopt the theme
        var root = document.documentElement;
        if ("__THEME_CLASS__" === "cx-theme-light") {
            root.style.setProperty("color-scheme", "light");
        } else {
            root.style.setProperty("color-scheme", "dark");
        }
    })();
    </script>
    """
    st.markdown(
        css.replace("__THEME_CLASS__", theme_class)
           .replace("__THEME_OVERRIDES__", theme_overrides)
           .replace("__ROOT_VARS__", root_vars),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Component Functions
# ---------------------------------------------------------------------------

def render_page_header(title: str, subtitle: str = ""):
    """Render a consistent premium page header with optional subtitle."""
    title_e = _escape(title)
    subtitle_e = _escape(subtitle)
    subtitle_html = f'<p class="cx-page-subtitle">{subtitle_e}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="cx-page-header">
        <div class="cx-page-eyebrow">Support intelligence workspace</div>
        <h1 class="cx-page-title">{title_e}</h1>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def render_command_bar(user: str, provider: str, online: bool, page: str):
    """Render a polished workspace command/status bar."""
    status = "Online" if online else "Local mode"
    st.markdown(f"""
    <div class="cx-command-bar">
        <div class="cx-command-left">
            <div class="cx-command-mark">C</div>
            <div>
                <div class="cx-command-title">CortexDesk AI</div>
                <div class="cx-command-meta">{_escape(page)} &mdash; {_escape(user)}</div>
            </div>
        </div>
        <div class="cx-command-status">
            <span class="cx-chip"><span class="cx-status-dot cx-status-{'online' if online else 'offline'}"></span>{_escape(provider)}</span>
            <span class="cx-chip">{status}</span>
            <span class="cx-chip">Risk engine active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_insight_grid(items: list):
    """Render compact operational insight tiles."""
    tiles = []
    for label, value, note in items:
        tiles.append(f"""
        <div class="cx-insight">
            <div class="cx-insight-label">{_escape(label)}</div>
            <div class="cx-insight-value">{_escape(value)}</div>
            <div class="cx-insight-note">{_escape(note)}</div>
        </div>
        """)
    st.markdown(f'<div class="cx-insight-grid">{"".join(tiles)}</div>', unsafe_allow_html=True)


def render_workflow_steps(steps: list):
    """Render a horizontal workflow strip."""
    html_steps = []
    for index, (title, text) in enumerate(steps, start=1):
        html_steps.append(f"""
        <div class="cx-workflow-step">
            <div class="cx-step-index">{index}</div>
            <div class="cx-step-title">{_escape(title)}</div>
            <div class="cx-step-text">{_escape(text)}</div>
        </div>
        """)
    st.markdown(f'<div class="cx-workflow">{"".join(html_steps)}</div>', unsafe_allow_html=True)


def render_metric_card(label: str, value, subtitle: str = "", color: str = ""):
    """Render a premium metric card."""
    label_e = _escape(label)
    value_e = _escape(value)
    subtitle_e = _escape(subtitle)
    color_style = f"color: {color};" if color else ""
    subtitle_html = f'<div class="cx-metric-subtitle">{subtitle_e}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="cx-metric">
        <div class="cx-metric-label">{label_e}</div>
        <div class="cx-metric-value" style="{color_style}">{value_e}</div>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def render_risk_badge(risk: str) -> str:
    """Return an HTML risk badge string. For use inside other components."""
    risk = str(risk or "low").lower()
    if risk not in {"high", "medium", "low"}:
        risk = "low"
    labels = {"high": "High Risk", "medium": "Medium Risk", "low": "Low Risk"}
    label = labels.get(risk, risk.title())
    return f'<span class="cx-risk-badge cx-risk-{risk}"><span class="cx-risk-dot cx-risk-dot-{risk}"></span>{label}</span>'


def render_risk_badge_standalone(risk: str):
    """Render a risk badge directly via st.markdown."""
    st.markdown(render_risk_badge(risk), unsafe_allow_html=True)


def render_decision_badge(decision: str) -> str:
    """Return an HTML decision badge string."""
    decision = str(decision or "respond").lower()
    safe_class = decision if decision in {"escalate", "respond_and_escalate", "respond"} else "respond"
    labels = {
        "escalate": "Escalate Immediately",
        "respond_and_escalate": "Respond &amp; Escalate",
        "respond": "Auto-Respond",
    }
    label = labels.get(decision, decision.replace("_", " ").title())
    return f'<span class="cx-decision-badge cx-decision-{safe_class}">{label}</span>'


def render_decision_badge_standalone(decision: str):
    """Render a decision badge directly."""
    st.markdown(render_decision_badge(decision), unsafe_allow_html=True)


def render_confidence_bar(label: str, value: float):
    """Render a styled animated confidence bar."""
    pct = max(0, min(100, int(float(value or 0) * 100)))
    label_e = _escape(label)
    # color based on value
    if pct >= 75:
        color = "linear-gradient(90deg, #34d399, #2dd4bf)"
    elif pct >= 50:
        color = "linear-gradient(90deg, #facc15, #fb923c)"
    else:
        color = "linear-gradient(90deg, #fb923c, #ff4d6d)"
    st.markdown(f"""
    <div class="cx-confidence-container">
        <div class="cx-confidence-label">
            <span>{label_e}</span>
            <span style="font-weight: 700;">{pct}%</span>
        </div>
        <div class="cx-confidence-track">
            <div class="cx-confidence-fill" style="width: {pct}%; background: {color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_confidence_bars(domain_confidence: float, risk_confidence: float):
    """Render both confidence bars (backward compatible)."""
    render_confidence_bar("Domain Detection", domain_confidence)
    render_confidence_bar("Risk Assessment", risk_confidence)


def render_ticket_card(ticket_data: dict):
    """Render a ticket as a premium styled card."""
    text = str(ticket_data.get("ticket_text", ticket_data.get("ticket", "")))
    display_text = text[:200] + "..." if len(text) > 200 else text
    domain = _escape(ticket_data.get("domain", "Unknown"))
    risk = ticket_data.get("risk", "low")
    decision = ticket_data.get("decision", "respond")
    timestamp = _escape(ticket_data.get("timestamp", ""))

    st.markdown(f"""
    <div class="cx-ticket-card">
        <div class="cx-ticket-header">
            <span class="cx-ticket-domain">{domain}</span>
            <span class="cx-ticket-time">{timestamp}</span>
        </div>
        <div class="cx-ticket-text">{_escape(display_text)}</div>
        <div class="cx-ticket-meta">
            {render_risk_badge(risk)}
            {render_decision_badge(decision)}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_doc_snippet(doc, index: int = 0):
    """Render a premium knowledge base document card with relevance bar."""
    if isinstance(doc, dict):
        text = doc.get("text", "")
        score = doc.get("score", 0)
        source = doc.get("source", "")
        reason = doc.get("reason", "")
    else:
        text = str(doc)
        score = 0
        source = ""
        reason = ""

    score_f = float(score) if score else 0.0
    score_pct = int(score_f * 100)

    # Score pill class
    if score_f >= 0.75:
        score_cls = "cx-doc-score-high"
        bar_color = "#34d399"
        score_label = f"{score_pct}% match"
    elif score_f >= 0.45:
        score_cls = "cx-doc-score-medium"
        bar_color = "#facc15"
        score_label = f"{score_pct}% match"
    elif score_f > 0:
        score_cls = "cx-doc-score-low"
        bar_color = "#7d90a8"
        score_label = f"{score_pct}% match"
    else:
        score_cls = "cx-doc-score-low"
        bar_color = "rgba(148,163,184,0.3)"
        score_label = ""

    source_display = source if source else f"Source {index + 1}"
    icon_letter = source_display[0].upper() if source_display else "K"
    score_pill = f'<span class="cx-doc-score-pill {score_cls}">{score_label}</span>' if score_label else ""
    reason_html = f'<div style="font-size:11.5px; color: var(--text-tertiary); margin-top:6px; font-style:italic;">{_escape(reason)}</div>' if reason else ""
    bar_html = f'<div class="cx-doc-relevance-bar" style="background: {bar_color}; width: {min(100, score_pct)}%;"></div>' if score_f > 0 else ""

    st.markdown(f"""
    <div class="cx-doc-card">
        {bar_html}
        <div class="cx-doc-card-header">
            <div class="cx-doc-card-left">
                <div class="cx-doc-card-icon">{icon_letter}</div>
                <div class="cx-doc-card-source">{_escape(source_display)}</div>
            </div>
            <div class="cx-doc-card-right">
                <span class="cx-doc-index-chip">#{index + 1}</span>
                {score_pill}
            </div>
        </div>
        <div class="cx-doc-card-body">
            {_escape(text)}
            {reason_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_trigger_tags(triggers: list):
    """Render trigger keywords as styled tags."""
    if not triggers:
        return
    tags_html = "".join(f'<span class="cx-trigger-tag">{_escape(t)}</span>' for t in triggers)
    st.markdown(f'<div style="margin: 8px 0; line-height: 2.2;">{tags_html}</div>', unsafe_allow_html=True)


def render_explainability_panel(result: dict):
    """Render the explainability panel for analysis results."""
    items = []
    items.append(("Domain Detected", result.get("domain", "Unknown")))
    if result.get("secondary_domains"):
        items.append(("Secondary Domains", ", ".join(result["secondary_domains"])))
    items.append(("Risk Level", result.get("risk", "low").title()))
    items.append(("Risk Category", result.get("category", "GENERAL").replace("_", " ").title()))
    items.append(("Confidence (Domain)", f'{int(result.get("domain_confidence", 0) * 100)}%'))
    items.append(("Confidence (Risk)", f'{int(result.get("risk_confidence", 0) * 100)}%'))
    items.append(("Analysis Pipeline", _format_source(result.get("analysis_source", ""))))

    items_html = ""
    for key, value in items:
        items_html += f"""
        <div class="cx-explain-item">
            <span class="cx-explain-key">{_escape(key)}</span>
            <span class="cx-explain-value">{_escape(value)}</span>
        </div>
        """

    st.markdown(f"""
    <div class="cx-explain-panel">
        {items_html}
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(title: str, message: str = "", icon: str = ""):
    """Render a professional empty state without exposing raw HTML markup."""
    st.markdown(f"### {title}")
    if message:
        st.caption(message)
    if icon:
        st.markdown(f"{icon}")


def render_status_indicator(label: str, status: str = "online"):
    """Render a status indicator with animated dot."""
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: var(--text-secondary);">
        <span class="cx-status-dot cx-status-{status}"></span>
        {_escape(label)}
    </div>
    """, unsafe_allow_html=True)


def render_activity_item(text: str, timestamp: str = "", risk: str = "low"):
    """Render an activity feed item with timeline styling."""
    dot_color = {
        "high": "var(--risk-critical)",
        "medium": "var(--risk-medium)",
        "low": "var(--risk-low)"
    }.get(risk, "var(--text-tertiary)")
    time_html = f'<div class="cx-activity-time">{_escape(timestamp)}</div>' if timestamp else ""
    st.markdown(f"""
    <div class="cx-activity-item">
        <div class="cx-activity-dot" style="background: {dot_color};"></div>
        <div class="cx-activity-content">
            <div class="cx-activity-text">{_escape(text)}</div>
            {time_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_letter_preview(letter_data: dict):
    """Render an escalation letter preview."""
    subject = _escape(letter_data.get("subject", "Escalation Letter"))
    body = _escape(letter_data.get("body", "")).replace("\n", "<br>")
    severity = letter_data.get("severity", "Medium")

    sev_map = {"Critical": "high", "High": "medium", "Medium": "low"}
    sev_class = sev_map.get(severity, "low")
    severity_badge = f'<span class="cx-risk-badge cx-risk-{sev_class}">{_escape(severity)} Priority</span>'

    st.markdown(f"""
    <div class="cx-letter-preview">
        <div style="margin-bottom: 16px;">{severity_badge}</div>
        <div class="cx-letter-subject">{subject}</div>
        {body}
    </div>
    """, unsafe_allow_html=True)


def render_chart_card(title: str, subtitle: str = ""):
    """Return context for wrapping a Streamlit chart in a premium card.
    Usage: render_chart_card_open(), then your chart, then render_chart_card_close().
    Since Streamlit doesn't support wrapping native widgets in custom HTML,
    this renders a styled header above the chart.
    """
    subtitle_html = f'<div class="cx-chart-card-subtitle">{_escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="cx-chart-card">
        <div class="cx-chart-card-header">
            <div>
                <div class="cx-chart-card-title">{_escape(title)}</div>
                {subtitle_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_analytics_header(title: str, subtitle: str = ""):
    """Render a premium header for analytics chart sections."""
    subtitle_html = f'<p style="font-size:12px; color: var(--text-tertiary); margin: 3px 0 0 0;">{_escape(subtitle)}</p>' if subtitle else ""
    st.markdown(f"""
    <div style="padding: 14px 0 8px 0; border-bottom: 1px solid var(--border-subtle); margin-bottom: 10px;">
        <div style="font-size: 14px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.2px;">{_escape(title)}</div>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def render_risk_distribution_bar(low: int, medium: int, high: int):
    """Render an animated segmented risk distribution bar."""
    total = low + medium + high
    if total == 0:
        return
    low_pct = low / total * 100
    med_pct = medium / total * 100
    high_pct = high / total * 100
    st.markdown(f"""
    <div style="margin: 4px 0 16px 0;">
        <div style="display: flex; height: 10px; border-radius: 5px; overflow: hidden; gap: 2px; margin-bottom: 12px;">
            <div style="width: {low_pct}%; background: var(--risk-low); border-radius: 5px; transition: width 0.8s ease;"></div>
            <div style="width: {med_pct}%; background: var(--risk-medium); border-radius: 5px; transition: width 0.8s ease;"></div>
            <div style="width: {high_pct}%; background: var(--risk-critical); border-radius: 5px; transition: width 0.8s ease;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-secondary);">
            <div style="display:flex;align-items:center;gap:5px;">
                <span class="cx-risk-dot cx-risk-dot-low"></span>
                <span>Low <strong style="color:var(--text-primary);">{low}</strong></span>
            </div>
            <div style="display:flex;align-items:center;gap:5px;">
                <span class="cx-risk-dot cx-risk-dot-medium"></span>
                <span>Medium <strong style="color:var(--text-primary);">{medium}</strong></span>
            </div>
            <div style="display:flex;align-items:center;gap:5px;">
                <span class="cx-risk-dot cx-risk-dot-high"></span>
                <span>High <strong style="color:var(--text-primary);">{high}</strong></span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_bulk_progress_summary(total: int, escalated: int, high_risk: int, responded: int):
    """Render a premium bulk processing summary card."""
    st.markdown(f"""
    <div class="cx-card" style="margin-top: 16px;">
        <div style="font-size: 15px; font-weight: 700; color: var(--text-primary); margin-bottom: 16px; letter-spacing: -0.3px;">
            Processing Complete
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
            <div style="text-align: center; padding: 14px; background: var(--bg-secondary); border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
                <div style="font-size: 26px; font-weight: 800; color: var(--text-primary); letter-spacing: -1px;">{total}</div>
                <div style="font-size: 11px; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px;">Processed</div>
            </div>
            <div style="text-align: center; padding: 14px; background: var(--risk-low-bg); border-radius: var(--radius-md); border: 1px solid rgba(52,211,153,0.2);">
                <div style="font-size: 26px; font-weight: 800; color: var(--risk-low); letter-spacing: -1px;">{responded}</div>
                <div style="font-size: 11px; font-weight: 600; color: var(--risk-low); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; opacity: 0.8;">Auto-Responded</div>
            </div>
            <div style="text-align: center; padding: 14px; background: var(--risk-medium-bg); border-radius: var(--radius-md); border: 1px solid rgba(250,204,21,0.2);">
                <div style="font-size: 26px; font-weight: 800; color: var(--risk-medium); letter-spacing: -1px;">{escalated}</div>
                <div style="font-size: 11px; font-weight: 600; color: var(--risk-medium); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; opacity: 0.8;">Escalated</div>
            </div>
            <div style="text-align: center; padding: 14px; background: var(--risk-critical-bg); border-radius: var(--radius-md); border: 1px solid rgba(255,77,109,0.2);">
                <div style="font-size: 26px; font-weight: 800; color: var(--risk-critical); letter-spacing: -1px;">{high_risk}</div>
                <div style="font-size: 11px; font-weight: 600; color: var(--risk-critical); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; opacity: 0.8;">High Risk</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_logo():
    """Render a minimal sidebar brand header without repeating the site logo."""
    st.markdown("""
    <div style="padding: 6px 0 18px 0;">
        <div>
            <div style="font-size: 15px; font-weight: 800; color: #e2f0fb; letter-spacing: -0.5px;">CortexDesk</div>
            <div style="font-size: 11px; color: #4a6480; font-weight: 500;">Support Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_nav_label(label: str):
    """Render a styled navigation section label in the sidebar."""
    st.markdown(f"""
    <div style="font-size: 10px; font-weight: 700; color: #3a5068; text-transform: uppercase;
                letter-spacing: 1px; padding: 10px 4px 4px 4px; margin-top: 4px;">{_escape(label)}</div>
    """, unsafe_allow_html=True)


def render_sidebar_footer(version: str = "v1.0"):
    """Render a premium sidebar footer with version."""
    st.markdown(f"""
    <div style="padding: 14px 0 4px 0; border-top: 1px solid rgba(45,212,191,0.08);
                font-size: 11px; color: #3a5068;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>CortexDesk AI</span>
            <span style="background: rgba(45,212,191,0.10); color: #2dd4bf;
                          padding: 2px 7px; border-radius: 999px; font-weight: 600;
                          font-size: 10px; border: 1px solid rgba(45,212,191,0.15);">{_escape(version)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_upload_zone_instructions():
    """Render premium upload zone instructions above the file uploader."""
    st.markdown("""
    <div class="cx-upload-zone" style="margin-bottom: 16px;">
        <div style="font-size: 32px; margin-bottom: 12px; opacity: 0.45;">⊞</div>
        <div class="cx-upload-title">Drop your CSV file here</div>
        <div class="cx-upload-subtitle">
            Upload a CSV with a ticket_text column.
            Each row will be analyzed individually through the full AI triage pipeline.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _format_source(source: str) -> str:
    """Format analysis source for display."""
    mapping = {
        "combined_llm":     "Combined LLM (single API call)",
        "separate_llm":     "Separate LLM calls",
        "separate_embedding": "Embedding classification + LLM risk",
        "separate_legacy":  "Legacy classification + LLM risk",
        "":                 "Not recorded",
    }
    return mapping.get(source, source.replace("_", " ").title())


def _escape(value) -> str:
    """Escape dynamic content before inserting it into unsafe HTML blocks."""
    return html.escape(str(value), quote=True)
