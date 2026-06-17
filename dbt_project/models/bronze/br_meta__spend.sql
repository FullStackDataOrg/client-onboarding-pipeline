SELECT
    campaign_id,
    campaign_name,
    date::DATE              AS spend_date,
    impressions::INTEGER    AS impressions,
    clicks::INTEGER         AS clicks,
    (spend_cents / 100.0)::DECIMAL(12, 2) AS spend_usd,
    'meta'                  AS platform,
    CURRENT_TIMESTAMP       AS _bronze_loaded_at
FROM {{ source('raw', 'meta_ads_spend') }}
