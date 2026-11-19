import csv, json, time
from confluent_kafka import Producer

producer = Producer({"bootstrap.servers": "localhost:9092"})
envoyes = 0
with open("data/creditcard.csv") as f:
    for i, row in enumerate(csv.DictReader(f), start=1):
        message = {k: float(v) for k, v in row.items()}
        message["transaction_id"] = i
        producer.produce("transactions", json.dumps(message).encode("utf-8"))
        producer.poll(0)
        envoyes += 1
        if envoyes >= 1000:      # limite pour le test
            break
        time.sleep(0.01)
producer.flush()
print("Transactions envoyées :", envoyes)
