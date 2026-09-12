{{ config(materialized='view') }}

SELECT
    region_id,
    EXTRACT(YEAR FROM CAST(time AS DATE)) AS harvest_year,
    SUM(precipitation_sum) AS total_rainfall_mm,
    AVG(temperature_2m_max) AS avg_max_temp
FROM {{ source('bronze', 'weather') }}
GROUP BY region_id, harvest_year