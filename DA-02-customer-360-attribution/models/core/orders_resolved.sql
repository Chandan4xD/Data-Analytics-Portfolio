SELECT o.*, COALESCE(m.customer_id, o.user_pseudo_id) AS customer_key
FROM {{ ref('orders') }} o
LEFT JOIN {{ ref('identity_map') }} m ON o.user_pseudo_id = m.user_pseudo_id
