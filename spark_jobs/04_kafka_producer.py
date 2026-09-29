import json
import time
import random
from datetime import datetime
from confluent_kafka import Producer

# 1. Configure the Kafka Producer to talk to your local Docker container
conf = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'climate-sensor-fleet'
}
producer = Producer(conf)

TOPIC_NAME = 'climate-sensors-raw'

def delivery_report(err, msg):
    """Callback triggered by Kafka once a message is successfully delivered or fails."""
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Delivered reading to Topic: {msg.topic()} | Partition: [{msg.partition()}]")

print(f"Starting IoT Sensor Simulation... sending data to '{TOPIC_NAME}'")
print("Press Ctrl+C to stop.")

try:
    while True:
        # 2. Generate a fake sensor reading
        # Simulating region_ids 1 through 5 (to match your region_lookup.csv)
        reading = {
            "sensor_id": f"SENS-{random.randint(100, 999)}",
            "region_id": f"R0{random.randint(1, 5)}",
            "temp_c": round(random.uniform(15.0, 35.0), 2),
            "rainfall_mm": round(random.uniform(0.0, 50.0), 2),
            "yield_tons": round(random.uniform(1.0, 10.0), 2),
            "timestamp": datetime.utcnow().isoformat()
        }

        # 3. Serialize to JSON and send to Kafka
        json_payload = json.dumps(reading)
        producer.produce(TOPIC_NAME, json_payload.encode('utf-8'), callback=delivery_report)
        
        # 4. Trigger delivery callbacks and pause before the next reading
        producer.poll(0)
        time.sleep(2)  # Wait 2 seconds before sending the next reading

except KeyboardInterrupt:
    print("\nStopping sensor simulation...")
finally:
    # Wait for any outstanding messages to be delivered and delivery reports received
    producer.flush()
    print("Producer shutdown complete.")