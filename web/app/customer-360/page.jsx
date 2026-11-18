"use client";
import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { useData, num, usd, ratio } from "../useData";
import { Section, Table } from "../ui";
import { TABLEAU_URL, REPO_URL } from "../config";

const MODELS = ["first_touch", "last_touch", "linear", "time_decay"];
const COLORS = ["#4e79a7", "#f28e2b", "#59a14f", "#b07aa1"];

export default function Customer360() {
  const compare = useData("mart_attribution_compare");
  const roi = useData("mart_channel_roi");
  const signals = useData("mart_budget_signals");
  const segments = useData("mart_rfm_segments");
  const [model, setModel] = useState("linear");

  const pivot = {};
  (compare || []).forEach((r) => {
    pivot[r.channel] = pivot[r.channel] || { channel: r.channel };
    pivot[r.channel][r.model] = num(r.attributed_revenue);
  });

  return (
    <>
      <h1>Customer 360 and Marketing Attribution</h1>
      <p className="note">
        GA4 sample e-commerce data (real) with a simulated CRM and simulated ad spend. This page shows exported results
        from a dbt run on BigQuery. Code: <a href={REPO_URL}>GitHub</a>.
      </p>

      <Section title="Revenue by channel under four attribution models" rows={compare}>
        <ResponsiveContainer width="100%" height={340}>
          <BarChart data={Object.values(pivot)}>
            <XAxis dataKey="channel" />
            <YAxis tickFormatter={(v) => "$" + v / 1000 + "k"} />
            <Tooltip formatter={(v) => usd(v)} />
            <Legend />
            {MODELS.map((m, i) => <Bar key={m} dataKey={m} fill={COLORS[i]} />)}
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Channel ROI and cost per order" note="Spend is simulated from session volume." rows={roi}>
        <select value={model} onChange={(e) => setModel(e.target.value)}>
          {MODELS.map((m) => <option key={m}>{m}</option>)}
        </select>
        <Table
          rows={(roi || []).filter((r) => r.model === model && r.spend_usd != null)}
          cols={[["Channel", "channel"], ["Spend", "spend_usd", usd], ["Attributed revenue", "attributed_revenue", usd],
                 ["ROAS", "roas", ratio], ["Cost per order", "cpa_usd", ratio]]}
        />
      </Section>

      <Section title="Where last-touch disagrees with the other models" rows={signals}>
        <Table
          rows={signals || []}
          cols={[["Channel", "channel"], ["ROAS last touch", "roas_last_touch", ratio],
                 ["ROAS other models", "roas_other_models_avg", ratio], ["Signal", "signal"]]}
        />
      </Section>

      <Section title="RFM segments" rows={segments}>
        <Table
          rows={segments || []}
          cols={[["Segment", "segment"], ["Customers", "customers"], ["Avg LTV", "avg_ltv_usd", usd],
                 ["Avg orders", "avg_orders"], ["Avg recency (days)", "avg_recency_days"]]}
        />
      </Section>

      <h2>Tableau dashboard</h2>
      {TABLEAU_URL ? <iframe src={TABLEAU_URL} title="Tableau dashboard" /> : <p className="empty">Tableau link not set yet (app/config.js).</p>}
    </>
  );
}
