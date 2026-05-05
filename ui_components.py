import streamlit as st

def render_metric_card(label, value, delta=None):
    st.metric(label=label, value=value, delta=delta)

def render_risk_badge(risk):
    if risk == "high":
        return "🔴 High Risk"
    elif risk == "medium":
        return "🟠 Medium Risk"
    return "🟢 Low Risk"

def render_decision_badge(decision):
    if decision == "escalate":
        return "⚠️ Escalate Immediately"
    elif decision == "respond_and_escalate":
        return "🔄 Respond & Escalate"
    return "✅ Respond"

def render_confidence_bars(domain_confidence, risk_confidence):
    st.markdown("**System Confidence:**")
    st.progress(domain_confidence, text=f"Domain Detection: {int(domain_confidence * 100)}%")
    st.progress(risk_confidence, text=f"Risk Assessment: {int(risk_confidence * 100)}%")

