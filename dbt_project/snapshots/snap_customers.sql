{% snapshot snap_customers %}

{{
    config(
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='check',
        check_cols=['plan_tier', 'email'],
    )
}}

-- Reads directly from raw.customers (not stg_customers) so we capture
-- every source change before any Silver-layer filtering.
-- On each `dbt snapshot` run, dbt compares check_cols against the current
-- snapshot and adds a new row with dbt_valid_from / dbt_valid_to when a
-- value changes — this is SCD Type 2 without hand-written SQL.
SELECT * FROM {{ source('raw', 'customers') }}

{% endsnapshot %}
