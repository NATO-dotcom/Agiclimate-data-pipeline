import pandas as pd
from sqlalchemy import create_engine
import boto3
import io

# 1. Postgres Connection
PG_URL = "postgresql://farm_admin:farm_password@127.0.0.1:5434/farm_management"
engine = create_engine(PG_URL)

# 2. MinIO (S3) Connection
# We use boto3 but point it to our local localhost port instead of the real AWS cloud
s3_client = boto3.client(
    's3',
    endpoint_url='http://127.0.0.1:9000',
    aws_access_key_id='minio_admin',
    aws_secret_access_key='minio_password',
    region_name='us-east-1' # Required by boto3, even for local MinIO
)

BUCKET_NAME = 'agri-data-lake'

def create_bucket_if_missing():
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        print(f"Bucket '{BUCKET_NAME}' already exists.")
    except Exception:
        print(f"Creating bucket '{BUCKET_NAME}'...")
        s3_client.create_bucket(Bucket=BUCKET_NAME)

def extract_and_upload(table_name):
    print(f"Extracting '{table_name}' from Postgres...")
    df = pd.read_sql_table(table_name, engine)
    
    print(f"Converting to Parquet and uploading to MinIO...")
    # Write the dataframe to a temporary buffer in memory
    parquet_buffer = io.BytesIO()
    df.to_parquet(parquet_buffer, engine='pyarrow', index=False)
    
    # Upload the buffer to MinIO
    file_key = f"bronze/crop_data/{table_name}.parquet"
    parquet_buffer.seek(0)
    s3_client.upload_fileobj(parquet_buffer, BUCKET_NAME, file_key)
    
    print(f"Successfully uploaded: s3://{BUCKET_NAME}/{file_key}\n")

if __name__ == "__main__":
    create_bucket_if_missing()
    
    tables = ['regions', 'fields', 'harvest_yields']
    for table in tables:
        extract_and_upload(table)
        
    print("Bronze layer extraction complete!")