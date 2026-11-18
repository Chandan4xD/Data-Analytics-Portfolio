WITH t AS (
  SELECT
    *,
    POW(0.5, days_before_order / {{ var('half_life_days') }}) AS decay_raw
  FROM {{ ref('attribution_touchpoints') }}
),
t2 AS (
  SELECT *, SUM(decay_raw) OVER (PARTITION BY order_key) AS decay_total FROM t
),
weighted AS (
  SELECT 'first_touch' AS model, order_key, channel, campaign, revenue_usd,
         IF(touch_idx = 1, 1.0, 0.0) AS weight
  FROM t2
  UNION ALL
  SELECT 'last_touch', order_key, channel, campaign, revenue_usd,
         IF(touch_idx = touch_count, 1.0, 0.0)
  FROM t2
  UNION ALL
  SELECT 'linear', order_key, channel, campaign, revenue_usd,
         1.0 / touch_count
  FROM t2
  UNION ALL
  SELECT 'time_decay', order_key, channel, campaign, revenue_usd,
         decay_raw / decay_total
  FROM t2
)
SELECT model, order_key, channel, campaign, weight, weight * revenue_usd AS attributed_revenue
FROM weighted
WHERE weight > 0
