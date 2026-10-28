
# pub.py
import pika
import sys

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Fanout exchange broadcasts to all bound queues
channel.exchange_declare(exchange='logs', exchange_type='fanout', durable=True)

message = ' '.join(sys.argv[1:]) or "info: broadcast message"
channel.basic_publish(exchange='logs', routing_key='', body=message.encode())
print(" [x] Sent:", message)
connection.close()
