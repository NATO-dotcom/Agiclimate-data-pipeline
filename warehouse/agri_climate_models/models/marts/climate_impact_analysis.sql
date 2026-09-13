{{ config(materialized='table') }}

WITH crops AS (
    SELECT * FROM {{ ref('stg_crops') }}
),

weather AS (
    SELECT * FROM {{ ref('stg_weather') }}
)

SELECT
    c.region_name,
    c.crop_type,
    c.harvest_year,
    c.yield_tons,
    w.total_rainfall_mm,
    w.avg_max_temp
FROM crops c
JOIN weather w
ON c.region_id = w.region_id 
AND c.harvest_year = w.harvest_year