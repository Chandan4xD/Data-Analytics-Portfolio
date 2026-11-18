SELECT
  segment,
  COUNT(*) AS customers,
  ROUND(SUM(ltv_usd), 2) AS total_revenue_usd,
  ROUND(AVG(ltv_usd), 2) AS avg_ltv_usd,
  ROUND(AVG(frequency), 2) AS avg_orders,
  ROUND(AVG(recency_days), 1) AS avg_recency_days
FROM {{ ref('mart_rfm') }}
GROUP BY segment
