SELECT model, order_key, SUM(weight) AS total_weight
FROM {{ ref('attribution_long') }}
GROUP BY model, order_key
HAVING ABS(SUM(weight) - 1) > 0.0001
