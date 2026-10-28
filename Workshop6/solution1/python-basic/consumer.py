
# consumer.py
import pika
import time

# Replace 'localhost' with the broker IP if running remotely
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello', durable=True)
# Don't dispatch a new message to this worker until it has processed and acknowledged the previous one
channel.basic_qos(prefetch_count=1)

def callback(ch, method, properties, body):
    msg = body.decode()
    print(" [x] Received:", msg)
    # Simulate processing time
    time.sleep(0.5)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='hello', on_message_callback=callback)
print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
