{{ config(materialized='table') }}

-- Grain: one row per (platform, campaign_id, spend_date).
-- Additive measures: impressions, clicks, spend_usd.
-- Semi-additive ratios (cpc_usd, ctr) are pre-computed for BI convenience
-- but must NOT be summed across rows — always recalculate from the additive measures.
SELECT
    {{ dbt_utils.generate_surrogate_key(['platform', 'campaign_id', 'spend_date']) }}   AS spend_key,
    {{ dbt_utils.generate_surrogate_key(['platform', 'campaign_id']) }}                  AS campaign_key,
    spend_date                                                                            AS date_key,
    platform,
    impressions,
    clicks,
    spend_usd,
    CASE WHEN clicks > 0
        THEN spend_usd / clicks
        ELSE 0
    END::DECIMAL(10, 4)                                                                   AS cpc_usd,
    CASE WHEN impressions > 0
        THEN clicks::FLOAT / impressions
        ELSE 0
    END::DECIMAL(10, 6)                                                                   AS ctr
FROM {{ ref('stg_spend') }}
