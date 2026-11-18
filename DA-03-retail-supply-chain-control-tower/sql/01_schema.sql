CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS ops;
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS raw.dataco (
  order_item_id BIGINT, order_id BIGINT, order_ts TIMESTAMP, ship_ts TIMESTAMP,
  product_id INT, product_name TEXT, category TEXT, qty INT,
  sales_usd NUMERIC, unit_price NUMERIC,
  real_days INT, scheduled_days INT, delivery_status TEXT
);
CREATE INDEX IF NOT EXISTS ix_raw_dataco_order_ts ON raw.dataco (order_ts);

CREATE TABLE IF NOT EXISTS core.suppliers (
  supplier_id TEXT PRIMARY KEY, supplier_name TEXT, base_lead_days INT
);
CREATE TABLE IF NOT EXISTS core.products (
  product_id INT PRIMARY KEY, product_name TEXT, category TEXT,
  supplier_id TEXT REFERENCES core.suppliers (supplier_id),
  unit_price NUMERIC, avg_daily_demand NUMERIC,
  reorder_point INT, reorder_qty INT, is_active BOOLEAN DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS core.sim_state (
  id INT PRIMARY KEY CHECK (id = 1), sim_now TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS core.order_items (
  order_item_id BIGINT PRIMARY KEY, order_id BIGINT, order_ts TIMESTAMP,
  product_id INT, qty INT, sales_usd NUMERIC
);
CREATE INDEX IF NOT EXISTS ix_order_items_ts ON core.order_items (order_ts);
CREATE TABLE IF NOT EXISTS core.shipments (
  order_item_id BIGINT PRIMARY KEY, supplier_id TEXT, ship_ts TIMESTAMP,
  scheduled_days INT, real_days INT, delay_days_injected INT,
  delivered_ts TIMESTAMP, cycle_ts TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_shipments_cycle ON core.shipments (cycle_ts);
CREATE INDEX IF NOT EXISTS ix_shipments_delivered ON core.shipments (delivered_ts);
CREATE TABLE IF NOT EXISTS core.purchase_orders (
  po_id BIGSERIAL PRIMARY KEY, product_id INT, supplier_id TEXT,
  placed_ts TIMESTAMP, arrive_ts TIMESTAMP, lead_days NUMERIC, qty INT,
  received BOOLEAN DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS core.inventory_snapshots (
  snapshot_ts TIMESTAMP, product_id INT, on_hand INT,
  PRIMARY KEY (snapshot_ts, product_id)
);

CREATE TABLE IF NOT EXISTS ops.delay_injection (
  supplier_id TEXT PRIMARY KEY, extra_days INT, active BOOLEAN DEFAULT TRUE,
  updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mart.kpi_hourly (
  cycle_ts TIMESTAMP PRIMARY KEY, computed_at TIMESTAMP DEFAULT now(),
  stockout_rate NUMERIC, on_time_delivery_pct NUMERIC,
  avg_supplier_lead_days NUMERIC, p90_supplier_lead_days NUMERIC,
  days_of_inventory NUMERIC, total_on_hand BIGINT, avg_daily_demand NUMERIC
);
CREATE TABLE IF NOT EXISTS mart.supplier_kpi (
  cycle_ts TIMESTAMP, supplier_id TEXT, shipments INT, avg_delay_days NUMERIC,
  PRIMARY KEY (cycle_ts, supplier_id)
);
CREATE TABLE IF NOT EXISTS mart.category_demand (
  cycle_ts TIMESTAMP, category TEXT, units INT, PRIMARY KEY (cycle_ts, category)
);
CREATE TABLE IF NOT EXISTS mart.anomalies (
  anomaly_id BIGSERIAL PRIMARY KEY, cycle_ts TIMESTAMP, metric TEXT, entity TEXT,
  value NUMERIC, baseline_mean NUMERIC, baseline_std NUMERIC, zscore NUMERIC, severity TEXT
);
CREATE TABLE IF NOT EXISTS mart.forecast (
  run_ts TIMESTAMP, category TEXT, forecast_date DATE,
  yhat NUMERIC, yhat_lower NUMERIC, yhat_upper NUMERIC
);
CREATE TABLE IF NOT EXISTS mart.forecast_accuracy (
  run_ts TIMESTAMP, category TEXT, mape NUMERIC, wape NUMERIC
);
CREATE TABLE IF NOT EXISTS mart.forecast_vs_stock (
  run_ts TIMESTAMP, category TEXT, on_hand_units NUMERIC, forecast_14d_units NUMERIC,
  days_of_cover NUMERIC, projected_stockout_date DATE
);
CREATE TABLE IF NOT EXISTS mart.scenario_results (
  supplier_id TEXT, delay_days INT, products_at_risk INT, units_short NUMERIC,
  revenue_at_risk NUMERIC, computed_at TIMESTAMP DEFAULT now(),
  PRIMARY KEY (supplier_id, delay_days)
);
CREATE TABLE IF NOT EXISTS mart.alert_log (
  alert_id BIGSERIAL PRIMARY KEY, alert_ts TIMESTAMP DEFAULT now(), alert_key TEXT,
  metric TEXT, entity TEXT, message TEXT, channel TEXT, delivered BOOLEAN
);
CREATE INDEX IF NOT EXISTS ix_alert_key ON mart.alert_log (alert_key, alert_ts);
CREATE TABLE IF NOT EXISTS mart.dq_checks (
  check_ts TIMESTAMP DEFAULT now(), cycle_ts TIMESTAMP, check_name TEXT,
  passed BOOLEAN, detail TEXT
);
