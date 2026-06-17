{{ config(materialized='table') }}

-- UNION ALL across platforms gives us a single conformed grain:
-- one row per (platform, campaign_id, spend_date).
-- Bronze handles the column renaming; Silver handles the unioning.
SELECT * FROM {{ ref('br_meta__spend') }}
UNION ALL
SELECT * FROM {{ ref('br_google__spend') }}
