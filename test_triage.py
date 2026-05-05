from triage import process_ticket
res = process_ticket("I ordered something on Amazon but also got charged twice on my card")
print(f"Domain: {res['domain']}")
print(f"Secondary: {res.get('secondary_domains')}")
print(f"Risk: {res['risk']}")
print(f"Decision: {res['decision']}")
print(f"Triggers: {res['triggers']}")
print(f"Response: {res['response']}")
