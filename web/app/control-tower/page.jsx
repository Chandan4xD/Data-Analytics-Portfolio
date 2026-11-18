"use client";
import { useState } from "react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { useData, num, usd, ratio, day } from "../useData";
import { Section, Table } from "../ui";
import { REPO_URL, DEMO_VIDEO_URL } from "../config";

export default function ControlTower() {
  const kpi = useData("kpi_hourly");
  const anomalies = useData("anomalies");
  const cover = useData("forecast_vs_stock");
  const scen = useData("scenario_results");
  const alerts = useData("alert_log");
  const [supplier, setSupplier] = useState("");
  const [delay, setDelay] = useState(7);

  const last = kpi && kpi.length ? kpi[kpi.length - 1] : null;
  const history = (kpi || []).map((r) => ({
    day: day(r.cycle_ts),
    stockout: +(num(r.stockout_rate) * 100).toFixed(1),
    onTime: +(num(r.on_time_delivery_pct) * 100).toFixed(1),
  }));
  const suppliers = [...new Set((scen || []).map((r) => r.supplier_id))];
  const sel = supplier || suppliers[0];
  const rows = (scen || []).filter((r) => r.supplier_id === sel).sort((a, b) => num(a.delay_days) - num(b.delay_days));
  const now = rows.find((r) => num(r.delay_days) === delay);

  return (
    <>
      <h1>Retail and Supply Chain Control Tower</h1>
      <p className="note">
        Snapshot of a pipeline run locally on replayed historical DataCo data. Suppliers and inventory are simulated.
        Code and setup: <a href={REPO_URL}>GitHub</a>.
      </p>

      <Section title="Current KPIs" rows={kpi}>
        {last && (
          <div className="cards">
            <div className="card"><b>{(num(last.stockout_rate) * 100).toFixed(1)}%</b><span>Stock-out rate</span></div>
            <div className="card"><b>{(num(last.on_time_delivery_pct) * 100).toFixed(1)}%</b><span>On-time delivery</span></div>
            <div className="card"><b>{ratio(last.avg_supplier_lead_days)}</b><span>Avg supplier lead time (days)</span></div>
            <div className="card"><b>{ratio(last.days_of_inventory)}</b><span>Days of inventory</span></div>
          </div>
        )}
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={history}>
            <XAxis dataKey="day" /><YAxis unit="%" /><Tooltip /><Legend />
            <Line type="monotone" dataKey="stockout" name="Stock-out rate" stroke="#e15759" dot={false} />
            <Line type="monotone" dataKey="onTime" name="On-time delivery" stroke="#4e79a7" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Anomalies" rows={anomalies}>
        <Table
          rows={[...(anomalies || [])].reverse().slice(0, 10)}
          cols={[["Date", "cycle_ts", day], ["Metric", "metric"], ["Entity", "entity"], ["Value", "value", ratio],
                 ["Baseline", "baseline_mean", ratio], ["z", "zscore", ratio], ["Severity", "severity"]]}
        />
      </Section>

      <Section title="What if a supplier is late?" rows={scen}>
        <select value={sel} onChange={(e) => setSupplier(e.target.value)}>
          {suppliers.map((s) => <option key={s}>{s}</option>)}
        </select>
        <label>Extra delay: {delay} days <input type="range" min="0" max="14" value={delay} onChange={(e) => setDelay(+e.target.value)} /></label>
        {now && (
          <div className="cards">
            <div className="card"><b>{now.products_at_risk}</b><span>Products at risk</span></div>
            <div className="card"><b>{num(now.units_short).toFixed(0)}</b><span>Units short</span></div>
            <div className="card"><b>{usd(now.revenue_at_risk)}</b><span>Revenue at risk</span></div>
          </div>
        )}
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={rows}>
            <XAxis dataKey="delay_days" /><YAxis /><Tooltip />
            <Bar dataKey="products_at_risk" name="Products at risk" fill="#f28e2b" />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Forecast demand vs current stock" rows={cover}>
        <Table
          rows={cover || []}
          cols={[["Category", "category"], ["On hand", "on_hand_units", (v) => num(v).toFixed(0)],
                 ["Forecast 14d", "forecast_14d_units", (v) => num(v).toFixed(0)], ["Days of cover", "days_of_cover", ratio],
                 ["Projected stock-out", "projected_stockout_date", day]]}
        />
      </Section>

      <Section title="Recent alerts" rows={alerts}>
        <Table rows={[...(alerts || [])].reverse().slice(0, 8)} cols={[["Time", "alert_ts", (v) => String(v).slice(0, 16)], ["Channel", "channel"], ["Message", "message"]]} />
      </Section>

      {DEMO_VIDEO_URL && (<><h2>Demo video</h2><iframe src={DEMO_VIDEO_URL} title="Demo video" allowFullScreen /></>)}
    </>
  );
}
