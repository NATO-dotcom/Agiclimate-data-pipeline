import duckdb

print("Initializing DuckDB and connecting to MinIO...")
con = duckdb.connect()

# Install and load the HTTP/S3 extensions
con.execute("INSTALL httpfs; LOAD httpfs; INSTALL aws; LOAD aws;")

# Configure DuckDB to authenticate with your local MinIO container
con.execute("""
    CREATE SECRET minio_secret (
        TYPE S3,
        KEY_ID 'minio_admin',
        SECRET 'minio_password',
        REGION 'us-east-1',
        ENDPOINT 'minio:9000',
        USE_SSL false,
        URL_STYLE 'path'
    );
""")

print("Building Silver Layer (Cleaning & Aggregating)...")

# 1. Aggregate daily weather into yearly totals per region
con.execute("""
    COPY (
        SELECT
            region_id,
            EXTRACT(YEAR FROM CAST(time AS DATE)) as harvest_year,
            SUM(precipitation_sum) as total_rainfall_mm,
            AVG(temperature_2m_max) as avg_max_temp
        FROM read_parquet('s3://agri-data-lake/bronze/climate_data/*.parquet')
        GROUP BY region_id, harvest_year
    ) TO 's3://agri-data-lake/silver/yearly_weather.parquet' (FORMAT PARQUET);
""")


# 2. Denormalize the Postgres crop tables into one wide table
con.execute("""
        COPY (
            SELECT
                r.region_id,
                r.region_name,
                h.crop_type,
                EXTRACT(YEAR FROM CAST(h.harvest_date AS DATE)) AS harvest_year,
                (h.yield_kg / 1000.0) AS yield_tons   
            FROM read_parquet('s3://agri-data-lake/bronze/crop_data/harvest_yields.parquet') h
            JOIN read_parquet('s3://agri-data-lake/bronze/crop_data/fields.parquet') f ON h.field_id = f.field_id
            JOIN read_parquet('s3://agri-data-lake/bronze/crop_data/regions.parquet') r ON f.region_id = r.region_id
        ) TO 's3://agri-data-lake/silver/denormalized_crops.parquet' (FORMAT PARQUET);
    """)

print("Building Gold Layer (Business Analytics)...")

# 3. Join Silver tables to create the final Climate Impact dataset
con.execute("""
    COPY (
        SELECT
            c.region_name,
            c.crop_type,
            c.harvest_year,
            c.yield_tons,
            w.total_rainfall_mm,
            w.avg_max_temp
        FROM read_parquet('s3://agri-data-lake/silver/denormalized_crops.parquet') c
        JOIN read_parquet('s3://agri-data-lake/silver/yearly_weather.parquet') w
        ON c.region_id = w.region_id AND c.harvest_year = w.harvest_year
    ) TO 's3://agri-data-lake/gold/climate_impact_analysis.parquet' (FORMAT PARQUET);
""")

print("DuckDB Transformations Complete!")