def check_risk(text, service):
    text = text.lower()

    for word in service["risk_words"]:
        if word in text:
            return "high"

    return "low"