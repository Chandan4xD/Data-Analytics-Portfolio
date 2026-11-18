WITH total AS (SELECT SUM(revenue_usd) AS rev FROM {{ ref('orders_resolved') }}),
m AS (SELECT model, SUM(attributed_revenue) AS rev FROM {{ ref('attribution_long') }} GROUP BY model)
SELECT m.model, m.rev, total.rev AS total_rev
FROM m CROSS JOIN total
WHERE ABS(m.rev - total.rev) > 1
