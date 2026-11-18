WITH o AS (
  SELECT order_key, customer_key, order_ts, revenue_usd FROM {{ ref('orders_resolved') }}
),
touches AS (
  SELECT
    o.order_key, o.customer_key, o.order_ts, o.revenue_usd,
    s.session_ts AS touch_ts, s.channel, s.campaign
  FROM o
  JOIN {{ ref('sessions_resolved') }} s
    ON s.customer_key = o.customer_key
   AND s.session_ts <= o.order_ts
   AND s.session_ts >= TIMESTAMP_SUB(o.order_ts, INTERVAL {{ var('lookback_days') }} DAY)
  WHERE s.channel NOT IN ('Internal', 'Unattributed')
),
fallback AS (
  SELECT
    o.order_key, o.customer_key, o.order_ts, o.revenue_usd,
    o.order_ts AS touch_ts, 'Unattributed' AS channel, CAST(NULL AS STRING) AS campaign
  FROM o
  WHERE o.order_key NOT IN (SELECT DISTINCT order_key FROM touches)
),
unioned AS (
  SELECT * FROM touches
  UNION ALL
  SELECT * FROM fallback
)
SELECT
  *,
  ROW_NUMBER() OVER (PARTITION BY order_key ORDER BY touch_ts, channel) AS touch_idx,
  COUNT(*) OVER (PARTITION BY order_key) AS touch_count,
  TIMESTAMP_DIFF(order_ts, touch_ts, HOUR) / 24.0 AS days_before_order
FROM unioned
