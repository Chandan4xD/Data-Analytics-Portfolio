SELECT
  model,
  channel,
  ROUND(SUM(attributed_revenue), 2) AS attributed_revenue,
  ROUND(SUM(weight), 2) AS attributed_orders,
  SAFE_DIVIDE(SUM(attributed_revenue), SUM(SUM(attributed_revenue)) OVER (PARTITION BY model)) AS revenue_share
FROM {{ ref('attribution_long') }}
GROUP BY model, channel
