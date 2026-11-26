import csv, json, time, os
from confluent_kafka import Producer

DELAY = float(os.getenv("PRODUCER_DELAY", "0.01"))   # secondes entre deux messages
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "1000"))

producer = Producer({"bootstrap.servers": "localhost:9092"})
envoyes = 0
with open("data/creditcard.csv") as f:
    for i, row in enumerate(csv.DictReader(f), start=1):
        message = {k: float(v) for k, v in row.items()}
        message["transaction_id"] = i
        producer.produce("transactions", json.dumps(message).encode("utf-8"))
        producer.poll(0)
        envoyes += 1
        if envoyes >= MAX_MESSAGES:      # limite pour le test
            break
        time.sleep(DELAY)
producer.flush()
print("Transactions envoyées :", envoyes)
