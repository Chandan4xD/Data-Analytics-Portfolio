import logging
from datetime import datetime, timedelta

import pandas as pd

from .db import execute, read_df

HORIZON = 14
HOLDOUT = 14
MIN_POINTS = HOLDOUT + 28
TOP_CATEGORIES = 12


def mape(actual, pred):
    pairs = [(a, p) for a, p in zip(actual, pred) if a > 0]
    return sum(abs(a - p) / a for a, p in pairs) / len(pairs) if pairs else None


def wape(actual, pred):
    total = sum(actual)
    return sum(abs(a - p) for a, p in zip(actual, pred)) / total if total > 0 else None


def _fit_predict(df, periods):
    from prophet import Prophet
    logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
    m = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=len(df) >= 365)
    m.fit(df)
    fc = m.predict(m.make_future_dataframe(periods=periods)).tail(periods)
    return fc


def run_forecast(conn):
    now = read_df(conn, "SELECT sim_now FROM core.sim_state WHERE id = 1").iloc[0, 0].to_pydatetime()
    daily = read_df(conn, """
        SELECT p.category, DATE(oi.order_ts) AS ds, SUM(oi.qty) AS y
        FROM core.order_items oi JOIN core.products p USING (product_id)
        GROUP BY 1, 2""")
    if daily.empty:
        return 0
    daily["ds"] = pd.to_datetime(daily["ds"])
    daily["y"] = daily["y"].astype(float)
    top = daily.groupby("category")["y"].sum().nlargest(TOP_CATEGORIES).index
    run_ts = datetime.now()
    fc_rows, acc_rows, cover_rows = [], [], []
    stock = read_df(conn, """
        SELECT p.category, SUM(i.on_hand) AS on_hand FROM core.inventory_snapshots i
        JOIN core.products p USING (product_id)
        WHERE i.snapshot_ts = (SELECT MAX(snapshot_ts) FROM core.inventory_snapshots) GROUP BY 1""")
    stock = dict(zip(stock["category"], stock["on_hand"]))

    for cat in top:
        s = daily[daily["category"] == cat].set_index("ds")["y"]
        s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="D"), fill_value=0.0)
        df = s.reset_index().rename(columns={"index": "ds", 0: "y"})
        df.columns = ["ds", "y"]
        if len(df) < MIN_POINTS:
            continue
        back = _fit_predict(df.iloc[:-HOLDOUT], HOLDOUT)
        actual = df["y"].iloc[-HOLDOUT:].tolist()
        pred = back["yhat"].clip(lower=0).tolist()
        acc_rows.append((run_ts, cat, mape(actual, pred), wape(actual, pred)))
        fc = _fit_predict(df, HORIZON)
        for r in fc.itertuples():
            fc_rows.append((run_ts, cat, r.ds.date(), max(0.0, float(r.yhat)),
                            max(0.0, float(r.yhat_lower)), max(0.0, float(r.yhat_upper))))
        demand14 = sum(max(0.0, float(v)) for v in fc["yhat"])
        on_hand = float(stock.get(cat, 0))
        per_day = demand14 / HORIZON
        cover = on_hand / per_day if per_day > 0 else None
        stockout = (now + timedelta(days=cover)).date() if cover is not None and cover <= 60 else None
        cover_rows.append((run_ts, cat, on_hand, demand14, cover, stockout))

    execute(conn, "DELETE FROM mart.forecast")
    execute(conn, "DELETE FROM mart.forecast_vs_stock")
    with conn.cursor() as cur:
        cur.executemany("""INSERT INTO mart.forecast (run_ts, category, forecast_date, yhat, yhat_lower, yhat_upper)
                           VALUES (%s, %s, %s, %s, %s, %s)""", fc_rows)
        cur.executemany("""INSERT INTO mart.forecast_accuracy (run_ts, category, mape, wape)
                           VALUES (%s, %s, %s, %s)""", acc_rows)
        cur.executemany("""INSERT INTO mart.forecast_vs_stock
            (run_ts, category, on_hand_units, forecast_14d_units, days_of_cover, projected_stockout_date)
            VALUES (%s, %s, %s, %s, %s, %s)""", cover_rows)
    conn.commit()
    return len(cover_rows)
