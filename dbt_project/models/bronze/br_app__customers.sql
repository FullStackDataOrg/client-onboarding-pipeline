SELECT
    customer_id::INTEGER    AS customer_id,
    email,
    full_name,
    plan_tier,
    signup_date::DATE       AS signup_date,
    _loaded_at::TIMESTAMP   AS _loaded_at,
    CURRENT_TIMESTAMP       AS _bronze_loaded_at
FROM {{ source('raw', 'customers') }}
