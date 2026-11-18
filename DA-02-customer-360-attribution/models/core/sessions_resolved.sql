SELECT s.*, COALESCE(m.customer_id, s.user_pseudo_id) AS customer_key
FROM {{ ref('sessions') }} s
LEFT JOIN {{ ref('identity_map') }} m ON s.user_pseudo_id = m.user_pseudo_id
