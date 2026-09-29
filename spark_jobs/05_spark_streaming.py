from pathlib import Path
import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.sql.functions import from_json, col

# 1. Setup paths and dynamic Spark versioning for the Kafka connector
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
REGIONS_PATH = str(PROJECT_ROOT / "region_lookup.csv")
spark_version = pyspark.__version__

# We must include the spark-sql-kafka package to talk to Kafka
spark = SparkSession.builder \
    .master("local[*]") \
    .appName("AgriClimate_SparkStreaming") \
    .config("spark.jars.packages", f"org.apache.spark:spark-sql-kafka-0-10_2.13:{spark_version}") \
    .getOrCreate()

# 2. Define the schema of the incoming JSON data from Kafka
sensor_schema = StructType([
    StructField("sensor_id", StringType(), True),
    StructField("region_id", StringType(), True),
    StructField("temp_c", DoubleType(), True),
    StructField("rainfall_mm", DoubleType(), True),
    StructField("yield_tons", DoubleType(), True),
    StructField("timestamp", StringType(), True)
])

print("Connecting to Kafka stream...")

# 3. Read the stream from Kafka
raw_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "climate-sensors-raw") \
    .option("startingOffsets", "latest") \
    .load()

# 4. Kafka sends data as raw bytes. Convert it to String, then parse the JSON
parsed_stream = raw_stream \
    .selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), sensor_schema).alias("data")) \
    .select("data.*")

# 5. Load the static batch lookup data
regions_df = spark.read.option("header", "true").csv(REGIONS_PATH)

# 6. Stream-Static Join: Join the live stream with the static CSV
enriched_stream = parsed_stream.join(regions_df, "region_id", "left")

print("Starting the live console sink...")

# 7. Output the joined stream to the console in micro-batches
query = enriched_stream.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# Keep the streaming job running indefinitely
query.awaitTermination()