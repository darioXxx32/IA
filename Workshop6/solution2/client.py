"""One farm worker for the RabbitMQ federated-learning protocol demo."""
import argparse
import json
import os
import time
import pika


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True, dest='client_id')
    parser.add_argument('--samples', required=True, type=int)
    parser.add_argument('--delta', required=True, type=float,
                        help='Toy local model update used for the transport demo')
    parser.add_argument('--delay', type=float, default=0)
    args = parser.parse_args()
    host = os.getenv('RABBITMQ_HOST', 'localhost')
    parameters = pika.ConnectionParameters(host=host, port=int(os.getenv('RABBITMQ_PORT', '5672')))
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange='fl.control', exchange_type='direct', durable=True)
    channel.exchange_declare(exchange='fl.updates', exchange_type='topic', durable=True)
    command_queue = f'fl.command.{args.client_id}'
    channel.queue_declare(queue=command_queue, durable=True)
    channel.queue_bind(exchange='fl.control', queue=command_queue, routing_key=args.client_id)
    channel.basic_qos(prefetch_count=1)
    # Keep confirm-waiting publishes off the consumer connection. Blocking Pika
    # can dispatch nested callbacks while waiting for confirms on a shared channel.
    publisher_connection = pika.BlockingConnection(parameters)
    publisher = publisher_connection.channel()
    publisher.exchange_declare(exchange='fl.updates', exchange_type='topic', durable=True)
    publisher.confirm_delivery()
    print(f'[{args.client_id}] READY; waiting for round command', flush=True)

    def handle(ch, method, properties, body):
        command = json.loads(body)
        if command.get('client_id') not in (None, args.client_id):
            ch.basic_ack(method.delivery_tag)
            return
        round_id = command['round_id']
        print(f'[{args.client_id}] received round={round_id}', flush=True)
        if args.delay:
            time.sleep(args.delay)
        global_weights = command['global_weights']
        updated = [float(w) + args.delta for w in global_weights]
        result = {
            'round_id': round_id,
            'client_id': args.client_id,
            'num_samples': args.samples,
            'weights': updated,
            'metrics': {'simulated_local_delta': args.delta},
        }
        try:
            publisher.basic_publish(
                exchange='fl.updates', routing_key=f'fit.{round_id}.{args.client_id}',
                body=json.dumps(result, separators=(',', ':')).encode(),
                properties=pika.BasicProperties(
                    content_type='application/json', delivery_mode=2,
                    message_id=f'{round_id}:{args.client_id}', correlation_id=round_id,
                    type='fit_result'), mandatory=True)
        except (pika.exceptions.NackError, pika.exceptions.UnroutableError):
            ch.basic_nack(method.delivery_tag, requeue=True)
            return
        ch.basic_ack(method.delivery_tag)
        print(f'[{args.client_id}] published update; command acknowledged', flush=True)
        ch.stop_consuming()

    channel.basic_consume(queue=command_queue, on_message_callback=handle, auto_ack=False)
    try:
        channel.start_consuming()
    finally:
        connection.close()
        publisher_connection.close()


if __name__ == '__main__':
    main()
