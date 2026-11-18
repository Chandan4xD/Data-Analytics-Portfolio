WITH base AS (
  SELECT
    customer_key, is_crm_matched, ltv_usd, orders AS frequency,
    DATE_DIFF(DATE '{{ var("as_of_date") }}', DATE(last_order_ts), DAY) AS recency_days
  FROM {{ ref('customer_profile') }}
),
scored AS (
  SELECT
    *,
    NTILE(5) OVER (ORDER BY recency_days DESC, customer_key) AS r_score,
    LEAST(frequency, 5) AS f_score,
    NTILE(5) OVER (ORDER BY ltv_usd ASC, customer_key) AS m_score
  FROM base
),
fm AS (
  SELECT *, (f_score + m_score) / 2.0 AS fm_score FROM scored
)
SELECT
  *,
  CASE
    WHEN r_score >= 4 AND fm_score >= 4 THEN 'Champions'
    WHEN r_score >= 3 AND fm_score >= 3 THEN 'Loyal'
    WHEN r_score >= 4 AND fm_score <  3 THEN 'Recent'
    WHEN r_score <= 2 AND fm_score >= 3 THEN 'At Risk'
    WHEN r_score =  3 AND fm_score <  3 THEN 'Needs Attention'
    ELSE 'Lost'
  END AS segment
FROM fm
