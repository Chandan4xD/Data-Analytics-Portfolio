{{ config(severity='warn') }}

WITH c AS (
  SELECT
    channel,
    MAX(IF(model = 'first_touch', attributed_revenue, NULL)) AS ft,
    MAX(IF(model = 'last_touch',  attributed_revenue, NULL)) AS lt
  FROM {{ ref('mart_attribution_compare') }}
  GROUP BY channel
)
SELECT 'first and last touch give identical results' AS issue
FROM (SELECT 1)
WHERE NOT EXISTS (SELECT 1 FROM c WHERE ABS(IFNULL(ft, 0) - IFNULL(lt, 0)) > 1)
