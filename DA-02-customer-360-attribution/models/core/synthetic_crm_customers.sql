WITH linked AS (
  SELECT customer_id, COUNT(*) AS linked_devices
  FROM {{ ref('identity_map') }}
  GROUP BY 1
),
first_orders AS (
  SELECT m.customer_id, MIN(o.order_ts) AS first_order_ts
  FROM {{ ref('identity_map') }} m
  JOIN {{ ref('orders') }} o ON o.user_pseudo_id = m.user_pseudo_id
  GROUP BY 1
)
SELECT
  l.customer_id,
  CONCAT('customer_', l.customer_id, '@example.com') AS email,
  TIMESTAMP_SUB(f.first_order_ts, INTERVAL MOD(ABS(FARM_FINGERPRINT(l.customer_id)), 365) DAY) AS crm_signup_ts,
  ['New York','Los Angeles','Chicago','Houston','Seattle','Austin','Boston','Denver']
    [OFFSET(MOD(ABS(FARM_FINGERPRINT(CONCAT('city|', l.customer_id))), 8))] AS city,
  MOD(ABS(FARM_FINGERPRINT(CONCAT('optin|', l.customer_id))), 100) < 60 AS email_opt_in,
  l.linked_devices
FROM linked l
JOIN first_orders f USING (customer_id)
