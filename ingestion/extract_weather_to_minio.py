import pandas as pd
import requests
from sqlalchemy import create_engine
import boto3
import io
import time

# 1. Postgres Connection (to get coordinates)
PG_URL = "postgresql://farm_admin:farm_password@127.0.0.1:5434/farm_management"
engine = create_engine(PG_URL)

# 2. MinIO Connection
s3_client = boto3.client(
    's3',
    endpoint_url='http://127.0.0.1:9000',
    aws_access_key_id='minio_admin',
    aws_secret_access_key='minio_password',
    region_name='us-east-1'
)
BUCKET_NAME = 'agri-data-lake'

def fetch_weather_for_regions():
    print("Reading region coordinates from Postgres...")
    df_regions = pd.read_sql_table('regions', engine)
    all_weather_data = []

    print("Fetching historical weather data from Open-Meteo...")
    
    for _, row in df_regions.iterrows():
        print(f"Pulling 2010-2020 climate data for {row['region_name']}...")
        
        # Open-Meteo Historical API endpoint
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": row['latitude'],
            "longitude": row['longitude'],
            "start_date": "2010-01-01",
            "end_date": "2020-12-31",
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
            "timezone": "Africa/Nairobi"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Convert JSON response to DataFrame
        df_weather = pd.DataFrame(data['daily'])
        df_weather['region_id'] = row['region_id']
        all_weather_data.append(df_weather)
        
        # Pause to respect free-tier API rate limits
        time.sleep(1)

    # Combine all regions into one massive DataFrame
    df_combined = pd.concat(all_weather_data, ignore_index=True)
    
    print("Converting to Parquet and uploading to MinIO...")
    parquet_buffer = io.BytesIO()
    df_combined.to_parquet(parquet_buffer, engine='pyarrow', index=False)
    
    file_key = "bronze/climate_data/historical_weather.parquet"
    parquet_buffer.seek(0)
    s3_client.upload_fileobj(parquet_buffer, BUCKET_NAME, file_key)
    
    print(f"Successfully uploaded: s3://{BUCKET_NAME}/{file_key}\n")

if __name__ == "__main__":
    fetch_weather_for_regions()