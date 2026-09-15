{{ config(materialized='table') }}

WITH crops AS (
    SELECT * FROM {{ ref('stg_crops') }}
),

weather AS (
    SELECT * FROM {{ ref('stg_weather') }}
),

categories AS (
    SELECT * FROM {{ ref('crop_categories') }}
)

SELECT
    c.region_name,
    c.crop_type,
    cat.crop_category,     -- Pulling the new category from our seed!
    c.harvest_year,
    c.yield_tons,
    w.total_rainfall_mm,
    w.avg_max_temp
FROM crops c
JOIN weather w
ON c.region_id = w.region_id 
AND c.harvest_year = w.harvest_year
LEFT JOIN categories cat
ON c.crop_type = cat.crop_type