import json
from collections import Counter

import pandas as pd
from triage import process_ticket


def _format_list(value):
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _summarize_scored_docs(scored_docs):
    if not scored_docs:
        return ""
    summary_lines = []
    for doc in scored_docs[:3]:
        source = doc.get("source", "?")
        score = doc.get("score", 0)
        reason = doc.get("reason", "")
        snippet = doc.get("text", "")
        summary_lines.append(f"{source}:{score:.2f}:{reason}")
    return " || ".join(summary_lines)


def _flatten_result(res):
    if not isinstance(res, dict):
        return {"error": f"Unexpected result type: {type(res).__name__}"}

    return {
        "ticket_id": res.get("ticket_id"),
        "ticket_text": res.get("ticket", ""),
        "domain": res.get("domain", ""),
        "secondary_domains": _format_list(res.get("secondary_domains", [])),
        "domain_confidence": res.get("domain_confidence"),
        "risk": res.get("risk", ""),
        "risk_confidence": res.get("risk_confidence"),
        "category": res.get("category", ""),
        "triggers": _format_list(res.get("triggers", [])),
        "decision": res.get("decision", ""),
        "reason": res.get("reason", ""),
        "analysis_source": res.get("analysis_source", ""),
        "retrieval_explanation": res.get("retrieval_explanation", ""),
        "scored_docs_summary": _summarize_scored_docs(res.get("scored_docs", [])),
        "response": res.get("response", ""),
        "error": res.get("error", ""),
        "raw_result": json.dumps(res, ensure_ascii=False),
    }


def run_bulk_processing(input_csv="data/tickets.csv", output_csv="output.csv"):
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"Error: {input_csv} not found.")
        return

    if "ticket_text" not in df.columns:
        print("Error: CSV must contain a column named `ticket_text`.")
        return

    results = []
    print(f"Processing {len(df)} tickets...")

    for index, row in df.iterrows():
        ticket = row["ticket_text"]
        res = process_ticket(ticket)
        results.append(res)
        domain = res.get("domain", "")
        risk = res.get("risk", "")
        error = res.get("error")
        status = f"[{index+1}/{len(df)}] Processed"
        if error:
            print(f"{status}: ERROR={error}")
        else:
            print(f"{status}: Domain={domain}, Risk={risk}")

    # Flatten results for CSV export
    flattened = [_flatten_result(res) for res in results]
    results_df = pd.DataFrame(flattened)
    results_df.to_csv(output_csv, index=False)

    # Print a simple processing summary
    risk_counter = Counter(res.get("risk", "unknown") if isinstance(res, dict) else "unknown" for res in results)
    decision_counter = Counter(res.get("decision", "unknown") if isinstance(res, dict) else "unknown" for res in results)
    error_count = sum(1 for res in results if isinstance(res, dict) and res.get("error"))

    print("\nProcessing summary:")
    print(f"  Total tickets: {len(results)}")
    print(f"  Errors: {error_count}")
    print(f"  Risk breakdown: {', '.join(f'{k}={v}' for k, v in risk_counter.items())}")
    print(f"  Decision breakdown: {', '.join(f'{k}={v}' for k, v in decision_counter.items())}")
    print(f"\nDone! Results saved to {output_csv}")


if __name__ == "__main__":
    run_bulk_processing()