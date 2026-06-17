-- Google Ads uses different column names vs Meta — this is the schema drift
-- the Bronze layer is designed to resolve before data reaches Silver.
SELECT
    ad_group_id             AS campaign_id,
    ad_group_name           AS campaign_name,
    report_date::DATE       AS spend_date,
    imps::INTEGER           AS impressions,
    clks::INTEGER           AS clicks,
    cost_usd::DECIMAL(12, 2) AS spend_usd,
    'google'                AS platform,
    CURRENT_TIMESTAMP       AS _bronze_loaded_at
FROM {{ source('raw', 'google_ads_spend') }}
