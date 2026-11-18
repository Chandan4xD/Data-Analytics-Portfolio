WITH daily AS (
  SELECT
    DATE(session_ts) AS spend_date,
    channel,
    COALESCE(campaign, '(none)') AS campaign,
    COUNT(*) AS sessions
  FROM {{ ref('sessions') }}
  WHERE channel IN ('Paid Search', 'Affiliate', 'Referral', 'Organic Search')
  GROUP BY 1, 2, 3
)
SELECT
  spend_date, channel, campaign, sessions,
  ROUND(
    sessions
    * CASE channel
        WHEN 'Paid Search'    THEN {{ var('cps_paid_search') }}
        WHEN 'Affiliate'      THEN {{ var('cps_affiliate') }}
        WHEN 'Referral'       THEN {{ var('cps_referral') }}
        WHEN 'Organic Search' THEN {{ var('cps_organic_search') }}
      END
    * (0.8 + 0.4 * MOD(ABS(FARM_FINGERPRINT(CONCAT(CAST(spend_date AS STRING), channel, campaign))), 1000) / 1000.0),
    2
  ) AS spend_usd
FROM daily
