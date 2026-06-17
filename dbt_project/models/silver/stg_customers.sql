{{ config(
    materialized='incremental',
    unique_key='customer_id',
    on_schema_change='append_new_columns'
) }}

-- unique_key makes re-runs idempotent: same customer_id on a second run
-- performs an UPDATE rather than inserting a duplicate row.
SELECT
    customer_id,
    email,
    full_name,
    plan_tier,
    signup_date,
    _loaded_at
FROM {{ ref('br_app__customers') }}

{% if is_incremental() %}
WHERE _loaded_at > (SELECT MAX(_loaded_at) FROM {{ this }})
{% endif %}
