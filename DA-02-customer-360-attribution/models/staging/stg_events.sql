WITH ev AS (
  SELECT
    user_pseudo_id,
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
    TIMESTAMP_MICROS(event_timestamp) AS event_ts,
    event_name,
    ecommerce.transaction_id AS transaction_id,
    ecommerce.purchase_revenue_in_usd AS revenue_usd,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'source')   AS src,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'medium')   AS med,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'campaign') AS camp
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '{{ var("start_suffix") }}' AND '{{ var("end_suffix") }}'
)
SELECT *
FROM ev
WHERE session_id IS NOT NULL
  AND (event_name IN ('purchase', 'session_start') OR src IS NOT NULL OR med IS NOT NULL)
