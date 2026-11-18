WITH spend AS (
  SELECT channel, campaign, SUM(spend_usd) AS spend_usd
  FROM {{ ref('synthetic_ad_spend') }} GROUP BY 1, 2
),
attr AS (
  SELECT channel, COALESCE(campaign, '(none)') AS campaign,
         SUM(attributed_revenue) AS attributed_revenue, SUM(weight) AS attributed_orders
  FROM {{ ref('attribution_long') }}
  WHERE model = 'linear'
  GROUP BY 1, 2
)
SELECT
  s.channel, s.campaign, s.spend_usd,
  IFNULL(a.attributed_revenue, 0) AS attributed_revenue,
  IFNULL(a.attributed_orders, 0) AS attributed_orders,
  SAFE_DIVIDE(IFNULL(a.attributed_revenue, 0) - s.spend_usd, s.spend_usd) AS roi,
  SAFE_DIVIDE(s.spend_usd, a.attributed_orders) AS cpa_usd
FROM spend s
LEFT JOIN attr a USING (channel, campaign)
