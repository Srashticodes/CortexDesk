import pandas as pd
from triage import process_ticket

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
        print(f"[{index+1}/{len(df)}] Processed: Domain={res['domain']}, Risk={res['risk']}")

    # Save output
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv, index=False)
    print(f"\nDone! Results saved to {output_csv}")

if __name__ == "__main__":
    run_bulk_processing()