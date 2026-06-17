{{ config(materialized='table') }}

-- Denormalised mart: daily aggregated spend by channel for BI dashboards.
-- Joins fct_daily_spend → dim_campaign (for channel/platform) → dim_date (for calendar attrs)
-- → channel_mapping seed (for human-readable channel labels).
SELECT
    d.date_day,
    d.year,
    d.quarter,
    d.month,
    d.iso_week,
    d.is_weekend,
    c.platform,
    cm.channel_name,
    cm.channel_group,
    COUNT(DISTINCT f.campaign_key)          AS active_campaigns,
    SUM(f.impressions)                      AS total_impressions,
    SUM(f.clicks)                           AS total_clicks,
    SUM(f.spend_usd)::DECIMAL(14, 2)        AS total_spend_usd,
    CASE WHEN SUM(f.impressions) > 0
        THEN SUM(f.clicks)::FLOAT / SUM(f.impressions)
        ELSE 0
    END::DECIMAL(10, 6)                     AS ctr,
    CASE WHEN SUM(f.clicks) > 0
        THEN SUM(f.spend_usd) / SUM(f.clicks)
        ELSE 0
    END::DECIMAL(10, 4)                     AS cpc_usd
FROM {{ ref('fct_daily_spend') }}   f
JOIN {{ ref('dim_campaign') }}      c  ON f.campaign_key = c.campaign_key
JOIN {{ ref('dim_date') }}          d  ON f.date_key     = d.date_key
LEFT JOIN {{ ref('channel_mapping') }} cm ON c.platform  = cm.platform
GROUP BY
    d.date_day, d.year, d.quarter, d.month, d.iso_week, d.is_weekend,
    c.platform, cm.channel_name, cm.channel_group
