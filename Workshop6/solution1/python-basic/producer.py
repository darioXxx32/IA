
# producer.py
import pika

# Replace 'localhost' with the broker IP if running remotely
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# Idempotent creation; durable queue survives broker restarts (metadata)
channel.queue_declare(queue='hello', durable=True)

message = "Hello Middleware!"
channel.basic_publish(
    exchange='',
    routing_key='hello',
    body=message.encode(),
    properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
)
print(" [x] Sent:", message)
connection.close()
