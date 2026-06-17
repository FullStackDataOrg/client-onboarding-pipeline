-- Singular test: returns rows that violate the contract.
-- dbt fails the test if this query returns any rows.
SELECT
    spend_key,
    spend_usd
FROM {{ ref('fct_daily_spend') }}
WHERE spend_usd < 0
