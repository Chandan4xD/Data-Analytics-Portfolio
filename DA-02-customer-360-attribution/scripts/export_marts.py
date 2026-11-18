import os, pathlib
from google.cloud import bigquery

PROJECT = os.environ["GCP_PROJECT"]
DATASET = os.environ.get("BQ_DATASET", "customer360")
TABLES = [
    "mart_attribution_compare", "mart_channel_roi", "mart_budget_signals",
    "mart_campaign_roi", "mart_rfm", "mart_rfm_segments",
    "customer_profile", "synthetic_ad_spend",
]
out = pathlib.Path("exports")
(out / "csv").mkdir(parents=True, exist_ok=True)
(out / "json").mkdir(parents=True, exist_ok=True)

client = bigquery.Client(project=PROJECT, location="US")
for t in TABLES:
    df = client.query(f"SELECT * FROM `{PROJECT}.{DATASET}.{t}`").to_dataframe()
    if t == "customer_profile":
        df = df.drop(columns=["email"], errors="ignore")
    df.to_csv(out / "csv" / f"{t}.csv", index=False)
    df.to_json(out / "json" / f"{t}.json", orient="records", date_format="iso")
    print(f"{t}: {len(df)} rows")
