WITH r AS (
  SELECT * FROM {{ ref('mart_channel_roi') }} WHERE spend_usd IS NOT NULL
),
p AS (
  SELECT
    channel,
    MAX(spend_usd) AS spend_usd,
    MAX(IF(model = 'last_touch', roas, NULL)) AS roas_last_touch,
    AVG(IF(model != 'last_touch', roas, NULL)) AS roas_other_models_avg,
    MIN(roas) AS roas_min_any_model,
    MAX(roas) AS roas_max_any_model
  FROM r
  GROUP BY channel
)
SELECT
  *,
  CASE
    WHEN roas_last_touch > 1.25 * roas_other_models_avg THEN 'Credit inflated by last-touch: do not scale on this alone'
    WHEN roas_last_touch < 0.80 * roas_other_models_avg THEN 'Undervalued by last-touch: candidate for more budget'
    ELSE 'Stable across models'
  END AS signal
FROM p
