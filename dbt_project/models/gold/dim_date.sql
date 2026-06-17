{{ config(materialized='table') }}

WITH date_spine AS (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2024-01-01' as date)",
        end_date="cast('2026-12-31' as date)"
    ) }}
)

SELECT
    date_day                                                    AS date_key,
    date_day,
    EXTRACT(year        FROM date_day)::INTEGER                 AS year,
    EXTRACT(quarter     FROM date_day)::INTEGER                 AS quarter,
    EXTRACT(month       FROM date_day)::INTEGER                 AS month,
    EXTRACT(week        FROM date_day)::INTEGER                 AS iso_week,
    EXTRACT(dayofweek   FROM date_day)::INTEGER                 AS day_of_week,
    CASE WHEN EXTRACT(dayofweek FROM date_day) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend
FROM date_spine
