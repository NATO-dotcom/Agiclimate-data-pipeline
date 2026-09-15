-- This test checks that neither yields nor rainfall are negative.
-- If any rows are returned, the pipeline will fail.

WITH crops AS (
    SELECT * FROM {{ ref('stg_crops') }}
),

weather AS (
    SELECT * FROM {{ ref('stg_weather') }}
)

SELECT 
    c.region_id,
    c.harvest_year,
    c.yield_tons,
    w.total_rainfall_mm
FROM crops c
JOIN weather w 
  ON c.region_id = w.region_id 
 AND c.harvest_year = w.harvest_year
WHERE c.yield_tons < 0 
   OR w.total_rainfall_mm < 0