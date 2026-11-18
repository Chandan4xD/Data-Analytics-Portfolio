WITH agg AS (
  SELECT
    customer_key,
    MIN(order_ts) AS first_order_ts,
    MAX(order_ts) AS last_order_ts,
    COUNT(*) AS orders,
    SUM(revenue_usd) AS ltv_usd,
    AVG(revenue_usd) AS avg_order_value_usd
  FROM {{ ref('orders_resolved') }}
  GROUP BY 1
)
SELECT
  a.*,
  c.customer_id IS NOT NULL AS is_crm_matched,
  c.email, c.city, c.email_opt_in, c.linked_devices
FROM agg a
LEFT JOIN {{ ref('synthetic_crm_customers') }} c ON c.customer_id = a.customer_key
