import pandas as pd

from .db import execute, read_df


def units_short(on_hand, daily_demand, lead_days, delay_days):
    return max(0.0, float(daily_demand) * (float(lead_days) + float(delay_days)) - float(on_hand))


def build_scenarios(products, max_delay=14):
    rows = []
    for supplier_id, g in products.groupby("supplier_id"):
        for d in range(0, max_delay + 1):
            short = [units_short(r.on_hand, r.daily_demand, r.lead_days, d) for r in g.itertuples()]
            at_risk = sum(1 for s in short if s > 0)
            revenue = sum(s * float(p) for s, p in zip(short, g.unit_price))
            rows.append((supplier_id, d, at_risk, round(sum(short), 2), round(revenue, 2)))
    return pd.DataFrame(rows, columns=["supplier_id", "delay_days", "products_at_risk",
                                       "units_short", "revenue_at_risk"])


def refresh_scenarios(conn, max_delay=14):
    now = read_df(conn, "SELECT sim_now FROM core.sim_state WHERE id = 1").iloc[0, 0].to_pydatetime()
    products = read_df(conn, """
        SELECT p.supplier_id, p.unit_price, s.base_lead_days AS lead_days,
               COALESCE(i.on_hand, 0) AS on_hand,
               COALESCE(d.units, 0) / 14.0 AS daily_demand
        FROM core.products p
        JOIN core.suppliers s USING (supplier_id)
        LEFT JOIN core.inventory_snapshots i
               ON i.product_id = p.product_id
              AND i.snapshot_ts = (SELECT MAX(snapshot_ts) FROM core.inventory_snapshots)
        LEFT JOIN (SELECT product_id, SUM(qty) AS units FROM core.order_items
                   WHERE order_ts >= %(now)s::timestamp - interval '14 days' AND order_ts < %(now)s
                   GROUP BY 1) d ON d.product_id = p.product_id
        WHERE p.is_active
    """, {"now": now})
    scen = build_scenarios(products, max_delay)
    execute(conn, "DELETE FROM mart.scenario_results")
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO mart.scenario_results
               (supplier_id, delay_days, products_at_risk, units_short, revenue_at_risk)
               VALUES (%s, %s, %s, %s, %s)""",
            [(r.supplier_id, int(r.delay_days), int(r.products_at_risk),
              float(r.units_short), float(r.revenue_at_risk)) for r in scen.itertuples()])
    conn.commit()
    return scen
