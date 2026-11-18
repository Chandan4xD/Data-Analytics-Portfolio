import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ct.db import get_conn, read_df

QUERIES = {
    "kpi_hourly": "SELECT * FROM mart.kpi_hourly ORDER BY cycle_ts",
    "supplier_kpi": "SELECT * FROM mart.supplier_kpi ORDER BY cycle_ts, supplier_id",
    "anomalies": "SELECT * FROM mart.anomalies ORDER BY cycle_ts",
    "forecast": "SELECT * FROM mart.forecast ORDER BY category, forecast_date",
    "forecast_accuracy": "SELECT * FROM mart.forecast_accuracy ORDER BY category",
    "forecast_vs_stock": "SELECT * FROM mart.forecast_vs_stock ORDER BY days_of_cover",
    "scenario_results": "SELECT * FROM mart.scenario_results ORDER BY supplier_id, delay_days",
    "alert_log": "SELECT * FROM mart.alert_log ORDER BY alert_ts",
    "dq_checks": "SELECT * FROM mart.dq_checks ORDER BY check_ts DESC LIMIT 100",
}
out = Path("exports")
(out / "json").mkdir(parents=True, exist_ok=True)
(out / "csv").mkdir(parents=True, exist_ok=True)
conn = get_conn()
for name, sql in QUERIES.items():
    df = read_df(conn, sql)
    for c in df.columns:
        if df[c].dtype == object and len(df) and df[c].map(lambda v: v.__class__.__name__).eq("Decimal").any():
            df[c] = df[c].astype(float)
    df.to_csv(out / "csv" / f"{name}.csv", index=False)
    df.to_json(out / "json" / f"{name}.json", orient="records", date_format="iso")
    print(f"{name}: {len(df)} rows")
