import argparse
import io
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from psycopg2.extras import execute_values

from ct.db import get_conn

RENAME = {
    "Order Item Id": "order_item_id", "Order Id": "order_id",
    "order date (DateOrders)": "order_ts", "shipping date (DateOrders)": "ship_ts",
    "Product Card Id": "product_id", "Product Name": "product_name", "Category Name": "category",
    "Order Item Quantity": "qty", "Order Item Total": "sales_usd", "Order Item Product Price": "unit_price",
    "Days for shipping (real)": "real_days", "Days for shipment (scheduled)": "scheduled_days",
    "Delivery Status": "delivery_status",
}
COLS = list(RENAME.values())


SUPPLIERS = [("S01", "Northwind Textiles", 3), ("S02", "Apex Sporting Goods", 5), ("S03", "Harbor Footwear", 7),
             ("S04", "Summit Outdoor", 4), ("S05", "Pacific Electronics", 10), ("S06", "Metro Apparel", 6),
             ("S07", "Atlas Fitness", 8), ("S08", "Beacon Accessories", 5)]


def parse_dates(s):
    out = pd.to_datetime(s, format="%m/%d/%Y %H:%M", errors="coerce")
    if out.isna().mean() > 0.5:
        out = pd.to_datetime(s, errors="coerce")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    args = ap.parse_args()

    df = pd.read_csv(args.csv, encoding="latin-1", usecols=lambda c: c in RENAME)
    missing = [c for c in RENAME if c not in df.columns]
    if missing:
        sys.exit(f"CSV is missing expected columns: {missing}\nFound: {list(df.columns)}")
    df = df.rename(columns=RENAME)
    df["order_ts"] = parse_dates(df["order_ts"])
    df["ship_ts"] = parse_dates(df["ship_ts"])
    df = df.dropna(subset=["order_ts", "product_id", "qty", "order_item_id"]).sort_values("order_ts")
    print(f"{len(df):,} order items, {df['order_ts'].min()} -> {df['order_ts'].max()}")

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""TRUNCATE raw.dataco, core.order_items, core.shipments, core.purchase_orders,
                       core.inventory_snapshots, core.sim_state, core.products, core.suppliers,
                       ops.delay_injection, mart.kpi_hourly, mart.supplier_kpi, mart.category_demand,
                       mart.anomalies, mart.forecast, mart.forecast_accuracy, mart.forecast_vs_stock,
                       mart.scenario_results, mart.alert_log, mart.dq_checks RESTART IDENTITY CASCADE""")
        buf = io.StringIO()
        df[COLS].to_csv(buf, index=False, header=False)
        buf.seek(0)
        cur.copy_expert(f"COPY raw.dataco ({','.join(COLS)}) FROM STDIN WITH (FORMAT csv)", buf)

        execute_values(cur, "INSERT INTO core.suppliers (supplier_id, supplier_name, base_lead_days) VALUES %s", SUPPLIERS)
        lead = {s[0]: s[2] for s in SUPPLIERS}

        days = max(1, (df["order_ts"].max() - df["order_ts"].min()).days + 1)
        g = df.groupby("product_id").agg(product_name=("product_name", "first"), category=("category", "first"),
                                         unit_price=("unit_price", "median"), units=("qty", "sum")).reset_index()
        products, inventory = [], []
        sim_start = df["order_ts"].min().normalize().to_pydatetime()
        for r in g.itertuples():
            sid = SUPPLIERS[int(r.product_id) % len(SUPPLIERS)][0]
            daily = float(r.units) / days
            reorder_point = max(1, math.ceil(daily * (lead[sid] + 3)))
            reorder_qty = max(1, math.ceil(daily * 14))
            products.append((int(r.product_id), r.product_name, r.category, sid, float(r.unit_price or 0),
                             round(daily, 4), reorder_point, reorder_qty))
            inventory.append((sim_start, int(r.product_id), max(1, math.ceil(daily * 30))))
        execute_values(cur, """INSERT INTO core.products (product_id, product_name, category, supplier_id,
            unit_price, avg_daily_demand, reorder_point, reorder_qty) VALUES %s""", products)
        execute_values(cur, "INSERT INTO core.inventory_snapshots (snapshot_ts, product_id, on_hand) VALUES %s", inventory)
        cur.execute("INSERT INTO core.sim_state (id, sim_now) VALUES (1, %s)", (sim_start,))
    conn.commit()
    print(f"Loaded {len(products)} products, {len(SUPPLIERS)} simulated suppliers. Simulation starts at {sim_start}.")


if __name__ == "__main__":
    main()
