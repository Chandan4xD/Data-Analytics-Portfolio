from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from psycopg2.extras import execute_values

from . import alerts, anomaly, config, kpis
from .db import execute, read_df


def sim_now(conn):
    return read_df(conn, "SELECT sim_now FROM core.sim_state WHERE id = 1").iloc[0, 0].to_pydatetime()


def replay_orders(conn, step_hours=None):
    step = step_hours or config.SIM_STEP_HOURS
    a = sim_now(conn)
    b = a + timedelta(hours=step)
    last = read_df(conn, "SELECT MAX(order_ts) AS m FROM raw.dataco").iloc[0, 0]
    if last is None or pd.isna(last) or a > last.to_pydatetime():
        raise RuntimeError("Replay reached the end of the dataset. Reload data or reset sim_state.")
    p = {"a": a, "b": b}
    execute(conn, """
        INSERT INTO core.order_items (order_item_id, order_id, order_ts, product_id, qty, sales_usd)
        SELECT order_item_id, order_id, order_ts, product_id, qty, sales_usd
        FROM raw.dataco
        WHERE order_ts >= %(a)s AND order_ts < %(b)s
        ON CONFLICT (order_item_id) DO NOTHING
    """, p)

    execute(conn, """
        INSERT INTO core.shipments (order_item_id, supplier_id, ship_ts, scheduled_days, real_days,
                                    delay_days_injected, delivered_ts, cycle_ts)
        SELECT r.order_item_id, p.supplier_id, COALESCE(r.ship_ts, r.order_ts), r.scheduled_days,
               r.real_days + COALESCE(d.extra_days, 0), COALESCE(d.extra_days, 0),
               COALESCE(r.ship_ts, r.order_ts) + make_interval(days => (r.real_days + COALESCE(d.extra_days, 0))::int),
               %(b)s
        FROM raw.dataco r
        JOIN core.products p ON p.product_id = r.product_id
        LEFT JOIN ops.delay_injection d ON d.supplier_id = p.supplier_id AND d.active
        WHERE r.order_ts >= %(a)s AND r.order_ts < %(b)s
          AND r.real_days IS NOT NULL AND r.scheduled_days IS NOT NULL
        ON CONFLICT (order_item_id) DO NOTHING
    """, p)
    execute(conn, "UPDATE core.sim_state SET sim_now = %(b)s WHERE id = 1", p)
    conn.commit()
    return b


def update_inventory(conn, step_hours=None):
    step = step_hours or config.SIM_STEP_HOURS
    now = sim_now(conn)
    start = now - timedelta(hours=step)

    prod = read_df(conn, """
        SELECT p.product_id, p.supplier_id, p.reorder_point, p.reorder_qty, s.base_lead_days
        FROM core.products p JOIN core.suppliers s USING (supplier_id) WHERE p.is_active""")
    inv = read_df(conn, """
        SELECT product_id, on_hand FROM core.inventory_snapshots
        WHERE snapshot_ts = (SELECT MAX(snapshot_ts) FROM core.inventory_snapshots)""")
    arrivals = read_df(conn, """
        SELECT po_id, product_id, qty FROM core.purchase_orders
        WHERE NOT received AND arrive_ts <= %(now)s""", {"now": now})
    demand = read_df(conn, """
        SELECT product_id, SUM(qty) AS demand FROM core.order_items
        WHERE order_ts >= %(a)s AND order_ts < %(b)s GROUP BY 1""", {"a": start, "b": now})

    df = prod.merge(inv, on="product_id", how="left")
    df = df.merge(arrivals.groupby("product_id", as_index=False)["qty"].sum().rename(columns={"qty": "received"}),
                  on="product_id", how="left")
    df = df.merge(demand, on="product_id", how="left")
    df["on_hand"] = (df["on_hand"].fillna(0) + df["received"].fillna(0).astype(float)
                     - df["demand"].fillna(0).astype(float)).clip(lower=0).astype(int)

    if len(arrivals):
        execute(conn, "UPDATE core.purchase_orders SET received = TRUE WHERE po_id = ANY(%(ids)s)",
                {"ids": [int(x) for x in arrivals["po_id"]]})

    open_po = read_df(conn, """
        SELECT product_id, SUM(qty) AS on_order FROM core.purchase_orders
        WHERE NOT received GROUP BY 1""")
    df = df.merge(open_po, on="product_id", how="left")
    df["on_order"] = df["on_order"].fillna(0).astype(float)

    inj = read_df(conn, "SELECT supplier_id, extra_days FROM ops.delay_injection WHERE active")
    extra = dict(zip(inj["supplier_id"], inj["extra_days"]))
    rng = np.random.default_rng(int(now.timestamp()))

    new_pos = []
    for r in df[(df["on_hand"] + df["on_order"]) <= df["reorder_point"]].itertuples():
        lead = max(1.0, float(r.base_lead_days) + float(extra.get(r.supplier_id, 0)) + float(rng.normal(0, 0.5)))
        new_pos.append((int(r.product_id), r.supplier_id, now, now + timedelta(days=lead), round(lead, 2), int(r.reorder_qty)))
    if new_pos:
        with conn.cursor() as cur:
            execute_values(cur, """INSERT INTO core.purchase_orders
                (product_id, supplier_id, placed_ts, arrive_ts, lead_days, qty) VALUES %s""", new_pos)

    with conn.cursor() as cur:
        execute_values(cur, """INSERT INTO core.inventory_snapshots (snapshot_ts, product_id, on_hand)
            VALUES %s ON CONFLICT DO NOTHING""",
                       [(now, int(r.product_id), int(r.on_hand)) for r in df.itertuples()])
    conn.commit()


def compute_kpis(conn, step_hours=None):
    step = step_hours or config.SIM_STEP_HOURS
    now = sim_now(conn)
    start = now - timedelta(hours=step)

    inv = read_df(conn, """
        SELECT i.product_id, i.on_hand FROM core.inventory_snapshots i
        JOIN core.products p USING (product_id)
        WHERE p.is_active AND i.snapshot_ts = (SELECT MAX(snapshot_ts) FROM core.inventory_snapshots)""")
    units14 = read_df(conn, """
        SELECT COALESCE(SUM(qty), 0) AS u FROM core.order_items
        WHERE order_ts >= %(now)s::timestamp - interval '14 days' AND order_ts < %(now)s""",
                      {"now": now}).iloc[0, 0]
    avg_daily = float(units14) / 14.0
    total_on_hand = int(inv["on_hand"].sum()) if len(inv) else 0

    ship = read_df(conn, """
        SELECT real_days, scheduled_days FROM core.shipments
        WHERE delivered_ts <= %(now)s AND delivered_ts > %(now)s::timestamp - interval '7 days'""", {"now": now})
    leads = read_df(conn, """
        SELECT lead_days FROM core.purchase_orders
        WHERE received AND arrive_ts <= %(now)s AND arrive_ts > %(now)s::timestamp - interval '30 days'""", {"now": now})

    lead_vals = [float(x) for x in leads["lead_days"]]
    row = (now, kpis.stockout_rate(inv["on_hand"]), kpis.on_time_pct(ship["real_days"], ship["scheduled_days"]),
           kpis.mean_or_none(lead_vals), kpis.p90(lead_vals),
           kpis.days_of_inventory(total_on_hand, avg_daily), total_on_hand, avg_daily)
    execute(conn, """
        INSERT INTO mart.kpi_hourly (cycle_ts, stockout_rate, on_time_delivery_pct, avg_supplier_lead_days,
            p90_supplier_lead_days, days_of_inventory, total_on_hand, avg_daily_demand)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (cycle_ts) DO UPDATE SET computed_at = now(),
            stockout_rate = EXCLUDED.stockout_rate, on_time_delivery_pct = EXCLUDED.on_time_delivery_pct,
            avg_supplier_lead_days = EXCLUDED.avg_supplier_lead_days,
            p90_supplier_lead_days = EXCLUDED.p90_supplier_lead_days,
            days_of_inventory = EXCLUDED.days_of_inventory, total_on_hand = EXCLUDED.total_on_hand,
            avg_daily_demand = EXCLUDED.avg_daily_demand""", row)


    execute(conn, """
        INSERT INTO mart.supplier_kpi (cycle_ts, supplier_id, shipments, avg_delay_days)
        SELECT cycle_ts, supplier_id, COUNT(*), AVG(real_days - scheduled_days)
        FROM core.shipments WHERE cycle_ts = %(now)s GROUP BY 1, 2
        ON CONFLICT (cycle_ts, supplier_id) DO NOTHING""", {"now": now})
    execute(conn, """
        INSERT INTO mart.category_demand (cycle_ts, category, units)
        SELECT %(now)s, p.category, COALESCE(SUM(oi.qty), 0)
        FROM core.products p
        LEFT JOIN core.order_items oi ON oi.product_id = p.product_id
             AND oi.order_ts >= %(a)s AND oi.order_ts < %(now)s
        GROUP BY p.category
        ON CONFLICT (cycle_ts, category) DO NOTHING""", {"now": now, "a": start})
    conn.commit()


def _scan(conn, table, key, val, metric, now, min_delta):
    hist = read_df(conn, f"""
        SELECT {key} AS entity, {val} AS v FROM (
          SELECT {key}, {val}, ROW_NUMBER() OVER (PARTITION BY {key} ORDER BY cycle_ts DESC) AS rn
          FROM mart.{table} WHERE cycle_ts < %(now)s) t
        WHERE rn <= %(n)s""", {"now": now, "n": config.Z_WINDOW})
    cur_rows = read_df(conn, f"SELECT {key} AS entity, {val} AS v FROM mart.{table} WHERE cycle_ts = %(now)s",
                       {"now": now})
    by_entity = {e: [float(x) for x in g["v"] if x is not None] for e, g in hist.groupby("entity")}
    found = []
    for r in cur_rows.itertuples():
        if r.v is None:
            continue
        z, mu, sd, flagged = anomaly.detect(by_entity.get(r.entity, []), float(r.v), config.Z_THRESHOLD,
                                            config.Z_WINDOW, config.Z_MIN_POINTS, min_delta)
        if flagged and z > 0:
            found.append((now, metric, r.entity, float(r.v), mu, sd, z, "high" if z >= 5 else "medium"))
    return found


def detect_anomalies(conn):
    now = sim_now(conn)
    found = (_scan(conn, "supplier_kpi", "supplier_id", "avg_delay_days", "supplier_delay_days", now,
                   config.MIN_DELTA_DELAY_DAYS)
             + _scan(conn, "category_demand", "category", "units", "category_demand_units", now,
                     config.MIN_DELTA_DEMAND_UNITS))
    if found:
        with conn.cursor() as cur:
            execute_values(cur, """INSERT INTO mart.anomalies
                (cycle_ts, metric, entity, value, baseline_mean, baseline_std, zscore, severity) VALUES %s""", found)
    conn.commit()
    return len(found)


def _candidates(conn, now):
    out = []
    k = read_df(conn, "SELECT * FROM mart.kpi_hourly WHERE cycle_ts = %(now)s", {"now": now})
    if len(k):
        r = k.iloc[0]
        if r.stockout_rate is not None and float(r.stockout_rate) > config.STOCKOUT_RATE_MAX:
            out.append(("stockout_rate|global|threshold", "stockout_rate", "global",
                        f"Stock-out rate {float(r.stockout_rate):.1%} is above {config.STOCKOUT_RATE_MAX:.0%}"))
        if r.on_time_delivery_pct is not None and not pd.isna(r.on_time_delivery_pct) \
                and float(r.on_time_delivery_pct) < config.ON_TIME_MIN:
            out.append(("on_time_delivery|global|threshold", "on_time_delivery_pct", "global",
                        f"On-time delivery {float(r.on_time_delivery_pct):.1%} is below {config.ON_TIME_MIN:.0%}"))
        if r.days_of_inventory is not None and not pd.isna(r.days_of_inventory) \
                and float(r.days_of_inventory) < config.DAYS_OF_INVENTORY_MIN:
            out.append(("days_of_inventory|global|threshold", "days_of_inventory", "global",
                        f"Days of inventory {float(r.days_of_inventory):.1f} is below {config.DAYS_OF_INVENTORY_MIN:.0f}"))
    a = read_df(conn, "SELECT * FROM mart.anomalies WHERE cycle_ts = %(now)s", {"now": now})
    for r in a.itertuples():
        out.append((f"{r.metric}|{r.entity}|anomaly|{r.severity}", r.metric, r.entity,
                    f"[{r.severity}] {r.metric} for {r.entity}: {float(r.value):.2f} vs baseline "
                    f"{float(r.baseline_mean):.2f} (z={float(r.zscore):.1f})"))
    return out


def send_alerts(conn):
    now = sim_now(conn)
    wall = datetime.now()
    sent = 0
    for key, metric, entity, message in _candidates(conn, now):
        last = read_df(conn, "SELECT MAX(alert_ts) AS t FROM mart.alert_log WHERE alert_key = %(k)s", {"k": key}).iloc[0, 0]
        last = None if last is None or pd.isna(last) else last.to_pydatetime()
        if not alerts.should_send(last, wall, config.ALERT_COOLDOWN_HOURS):
            continue
        delivered, channel = True, "console"
        if config.SLACK_WEBHOOK:
            channel = "slack"
            try:
                alerts.post_slack(config.SLACK_WEBHOOK, f":warning: Control Tower: {message}")
            except Exception as exc:
                delivered = False
                message = f"{message} (delivery failed: {exc})"
        else:
            print(f"ALERT: {message}")
        execute(conn, """INSERT INTO mart.alert_log (alert_key, metric, entity, message, channel, delivered)
                         VALUES (%s, %s, %s, %s, %s, %s)""", (key, metric, entity, message, channel, delivered))
        sent += 1
    conn.commit()
    return sent


def run_dq(conn):
    now = sim_now(conn)
    checks = {
        "no_null_keys_in_order_items": read_df(conn, """SELECT COUNT(*) AS n FROM core.order_items
            WHERE product_id IS NULL OR qty IS NULL OR order_ts IS NULL""").iloc[0, 0],
        "no_orphan_order_items": read_df(conn, """SELECT COUNT(*) AS n FROM core.order_items oi
            LEFT JOIN core.products p USING (product_id) WHERE p.product_id IS NULL""").iloc[0, 0],
        "no_negative_inventory": read_df(conn, """SELECT COUNT(*) AS n FROM core.inventory_snapshots
            WHERE on_hand < 0""").iloc[0, 0],
        "kpi_row_exists_for_cycle": 1 - int(read_df(conn, "SELECT COUNT(*) AS n FROM mart.kpi_hourly WHERE cycle_ts = %(now)s",
                                                    {"now": now}).iloc[0, 0] > 0),
        "no_duplicate_shipments": read_df(conn, """SELECT COUNT(*) - COUNT(DISTINCT order_item_id) AS n
            FROM core.shipments""").iloc[0, 0],
    }
    rows = [(now, name, int(bad) == 0, f"{int(bad)} offending rows") for name, bad in checks.items()]
    with conn.cursor() as cur:
        execute_values(cur, "INSERT INTO mart.dq_checks (cycle_ts, check_name, passed, detail) VALUES %s", rows)
    conn.commit()
    failed = [r[1] for r in rows if not r[2]]
    if failed:
        raise RuntimeError(f"Data quality checks failed: {failed}")


def run_cycle(conn, step_hours=None):
    from .whatif import refresh_scenarios
    replay_orders(conn, step_hours)
    update_inventory(conn, step_hours)
    compute_kpis(conn, step_hours)
    refresh_scenarios(conn)
    n_anom = detect_anomalies(conn)
    n_alerts = send_alerts(conn)
    run_dq(conn)
    return n_anom, n_alerts
