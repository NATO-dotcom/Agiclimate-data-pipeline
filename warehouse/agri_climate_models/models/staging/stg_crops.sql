{{ config(materialized='view') }}

WITH yields AS (
    SELECT * FROM {{ source('bronze', 'yields') }}
),

fields AS (
    SELECT * FROM {{ source('bronze', 'fields') }}
),

regions AS (
    SELECT * FROM {{ source('bronze', 'regions') }}
)

SELECT
    r.region_id,
    r.region_name,
    y.crop_type,
    EXTRACT(YEAR FROM CAST(y.harvest_date AS DATE)) AS harvest_year,
    {{ convert_kg_to_tons('y.yield_kg') }} AS yield_tons
FROM yields y
JOIN fields f ON y.field_id = f.field_id
JOIN regions r ON f.region_id = r.region_id