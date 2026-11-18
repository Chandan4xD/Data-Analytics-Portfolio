WITH buyers AS (
  SELECT DISTINCT user_pseudo_id FROM {{ ref('orders') }}
),
matched AS (
  SELECT
    user_pseudo_id,
    COUNT(*) OVER () * {{ var('crm_id_space_multiplier') }} AS id_space
  FROM buyers
  WHERE MOD(ABS(FARM_FINGERPRINT(CONCAT('match|', user_pseudo_id))), 100) < {{ var('crm_match_pct') }}
)
SELECT
  user_pseudo_id,
  CONCAT('C', LPAD(CAST(MOD(ABS(FARM_FINGERPRINT(CONCAT('cust|', user_pseudo_id))), id_space) AS STRING), 7, '0')) AS customer_id,
  'email_login (simulated)' AS match_rule
FROM matched
