import streamlit as st
import pandas as pd
from ui_components import render_metric_card, render_risk_badge, render_decision_badge, render_confidence_bars
from triage import process_ticket
from database import init_db, get_history
import base64

# --- Setup ---
st.set_page_config(page_title="CortexDesk ", layout="wide", initial_sidebar_state="expanded")
init_db()

# --- Custom CSS for SaaS Look ---
def local_css():
    st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    /* Dark mode toggle handling */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #0e1117;
        }
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    .ticket-card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #3b82f6;
        margin-bottom: 15px;
    }
    .doc-snippet {
        background-color: #f1f3f5;
        border-radius: 4px;
        padding: 10px;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
        margin-bottom: 5px;
        color: #333;
    }
    @media (prefers-color-scheme: dark) {
        .doc-snippet {
            background-color: #2b2b2b;
            color: #e0e0e0;
            border: 1px solid #444;
        }
    }
    /* Hide index on dataframe */
    .row_heading.level0 {display:none}
    .blank {display:none}
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- Auth ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; margin-top: 100px;'>🔒 CortexDesk Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                if username == "admin" and password == "admin":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials (try admin/admin)")
    st.stop()

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("## 🧠 CortexDesk")
    st.markdown("---")
    page = st.radio("Navigation", ["📊 Dashboard", "🔍 Analyze Ticket", "📜 History", "📂 Bulk Upload"])
    st.markdown("---")
    st.markdown("Theme follows system preferences.")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

# --- Page: Dashboard ---
if page == "📊 Dashboard":
    st.title("Analytics Dashboard")
    history_df = get_history()
    
    if history_df.empty:
        st.info("No tickets processed yet. Go to 'Analyze Ticket' or 'Bulk Upload' to start.")
    else:
        total_tickets = len(history_df)
        escalated = len(history_df[history_df["decision"] == "escalate"])
        escalation_rate = (escalated / total_tickets) * 100 if total_tickets > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Total Tickets Processed", total_tickets)
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Escalated Tickets", escalated)
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Escalation Rate", f"{escalation_rate:.1f}%")
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("### Domain Distribution")
        domain_counts = history_df["domain"].value_counts().reset_index()
        domain_counts.columns = ["Domain", "Count"]
        st.bar_chart(domain_counts.set_index("Domain"))

# --- Page: Analyze Ticket ---
elif page == "🔍 Analyze Ticket":
    st.title("Analyze Support Ticket")
    
    st.markdown("Enter a customer support query to automatically classify, assess risk, and generate a response.")
    
    with st.form("analyze_form"):
        ticket = st.text_area("📝 Ticket Content", height=150, placeholder="e.g., My Visa card was charged for an unauthorized transaction...", help="Include details for better accuracy.")
        submitted = st.form_submit_button("🚀 Analyze Ticket", type="primary")
        
    if submitted:
        if not ticket.strip():
            st.error("Please enter a ticket before analyzing.")
        else:
            with st.spinner("Analyzing ticket with CortexDesk AI..."):
                result = process_ticket(ticket)
            
            st.markdown("### Analysis Results")
            
            # Key Metrics Cards
            col1, col2, col3 = st.columns(3)
            
            domain_text = result['domain']
            if result.get('secondary_domains'):
                domain_text += f" (Secondary: {', '.join(result['secondary_domains'])})"
                
            col1.info(f"**🌐 Domain:**\n\n{domain_text}")
            col2.warning(f"**⚠️ Risk Level:**\n\n{render_risk_badge(result['risk'])}")
            col3.success(f"**📌 Decision:**\n\n{render_decision_badge(result['decision'])}")

            # 🔥 Risk Explanation (ADD THIS BLOCK)
            if result["risk"] == "high":
                st.error("🚨 High risk detected: This may involve security or fraud. Immediate action is recommended.")

            elif result["risk"] == "medium":
                st.info("ℹ️ Medium risk: This indicates a potential financial or account issue, but not confirmed fraud.")

            else:
                st.success("✅ Low risk: This appears to be a standard support query.")
            
            # Confidence & Reason
            st.markdown("---")
            render_confidence_bars(result["domain_confidence"], result["risk_confidence"])
            
            st.markdown("### 🧠 Reasoning")
            st.markdown(f"{result['reason']}")
            if result.get('triggers'):
                st.markdown(f"**Triggers Detected:** `{', '.join(result['triggers'])}`")
            
            # Response
            st.markdown("### 💬 Suggested Response")

            st.success(result["response"])
            
            # Retrieved Docs
            if result.get("docs"):
                st.markdown("### 📚 Relevant Knowledge Base Entries")
                for i, doc in enumerate(result["docs"]):
                    st.markdown(f"<div class='doc-snippet'><b>Snippet {i+1}:</b> {doc}</div>", unsafe_allow_html=True)

# --- Page: History ---
elif page == "📜 History":
    st.title("Ticket History")
    history_df = get_history()
    
    if history_df.empty:
        st.info("No tickets in history.")
    else:
        # Filters
        col1, col2 = st.columns(2)
        domain_filter = col1.selectbox("Filter by Domain", ["All"] + list(history_df["domain"].unique()))
        risk_filter = col2.selectbox("Filter by Risk", ["All"] + list(history_df["risk"].unique()))
        
        filtered_df = history_df.copy()
        if domain_filter != "All":
            filtered_df = filtered_df[filtered_df["domain"] == domain_filter]
        if risk_filter != "All":
            filtered_df = filtered_df[filtered_df["risk"] == risk_filter]
            
        st.dataframe(filtered_df[["timestamp", "ticket_text", "domain", "risk", "decision", "domain_confidence", "risk_confidence"]], use_container_width=True)
        
        # CSV Export
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download History as CSV",
            data=csv,
            file_name="cortexdesk_history.csv",
            mime="text/csv",
        )

# --- Page: Bulk Upload ---
elif page == "📂 Bulk Upload":
    st.title("Bulk Ticket Processing")
    st.markdown("Upload a CSV file containing a column named `ticket_text`.")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            if "ticket_text" not in df.columns:
                st.error("CSV must contain a column named `ticket_text`.")
            else:
                st.info(f"Loaded {len(df)} tickets. Ready to process.")
                
                if st.button("▶️ Start Processing", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    results = []
                    total = len(df)
                    
                    for index, row in df.iterrows():
                        ticket = row["ticket_text"]
                        status_text.text(f"Processing ticket {index+1}/{total}...")
                        res = process_ticket(ticket)
                        results.append(res)
                        progress_bar.progress((index + 1) / total)
                        
                    status_text.text("Processing complete!")
                    st.success(f"Successfully processed {total} tickets.")
                    
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df[["ticket", "domain", "risk", "decision"]].head(10))
                    
                    # CSV Export
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name="bulk_processing_results.csv",
                        mime="text/csv",
                    )
        except Exception as e:
            st.error(f"Error reading CSV: {e}")