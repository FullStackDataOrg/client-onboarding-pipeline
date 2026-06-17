{{ config(materialized='table') }}

-- Surrogate key combines platform + campaign_id so that a Meta campaign and a
-- Google campaign that happen to share a business ID remain distinct rows.
SELECT
    {{ dbt_utils.generate_surrogate_key(['platform', 'campaign_id']) }} AS campaign_key,
    campaign_id,
    campaign_name,
    platform,
    MIN(spend_date) AS first_seen_date,
    MAX(spend_date) AS last_seen_date
FROM {{ ref('stg_spend') }}
GROUP BY platform, campaign_id, campaign_name
