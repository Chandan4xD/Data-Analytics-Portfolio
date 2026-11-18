WITH base AS (
  SELECT
    user_pseudo_id,
    session_id,
    MIN(event_ts) AS session_ts,
    ARRAY_AGG(
      IF(src IS NOT NULL OR med IS NOT NULL, STRUCT(src, med, camp), NULL)
      IGNORE NULLS ORDER BY event_ts LIMIT 1
    )[SAFE_OFFSET(0)] AS s
  FROM {{ ref('stg_events') }}
  GROUP BY 1, 2
)
SELECT
  user_pseudo_id,
  session_id,
  CONCAT(user_pseudo_id, '-', CAST(session_id AS STRING)) AS session_key,
  session_ts,
  s.src  AS source,
  s.med  AS medium,
  s.camp AS campaign,
  {{ classify_channel('s.src', 's.med') }} AS channel
FROM base
