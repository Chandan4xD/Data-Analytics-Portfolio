WITH spend AS (
  SELECT channel, SUM(spend_usd) AS spend_usd FROM {{ ref('synthetic_ad_spend') }} GROUP BY 1
)
SELECT
  a.model,
  a.channel,
  a.attributed_revenue,
  a.attributed_orders,
  s.spend_usd,
  SAFE_DIVIDE(a.attributed_revenue - s.spend_usd, s.spend_usd) AS roi,
  SAFE_DIVIDE(a.attributed_revenue, s.spend_usd) AS roas,
  SAFE_DIVIDE(s.spend_usd, a.attributed_orders) AS cpa_usd
FROM {{ ref('mart_attribution_compare') }} a
LEFT JOIN spend s USING (channel)
