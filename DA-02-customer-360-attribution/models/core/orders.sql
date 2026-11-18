WITH purchases AS (
  SELECT
    user_pseudo_id, session_id, event_ts, revenue_usd,
    COALESCE(
      NULLIF(transaction_id, '(not set)'),
      CONCAT(user_pseudo_id, '-', CAST(session_id AS STRING), '-', CAST(UNIX_MICROS(event_ts) AS STRING))
    ) AS order_key
  FROM {{ ref('stg_events') }}
  WHERE event_name = 'purchase' AND IFNULL(revenue_usd, 0) > 0
)
SELECT
  order_key,
  ARRAY_AGG(user_pseudo_id ORDER BY event_ts LIMIT 1)[OFFSET(0)] AS user_pseudo_id,
  ARRAY_AGG(session_id ORDER BY event_ts LIMIT 1)[OFFSET(0)]     AS session_id,
  MIN(event_ts)    AS order_ts,
  MAX(revenue_usd) AS revenue_usd
FROM purchases
GROUP BY order_key
