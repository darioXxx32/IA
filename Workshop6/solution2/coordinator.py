"""Coordinator: broadcast a round, collect a quorum, and FedAvg model updates."""
import argparse
import json
import os
import time
import uuid
import pika


def weighted_average(updates):
    if not updates or any(u['num_samples'] <= 0 for u in updates):
        raise ValueError('Need non-empty updates with positive sample counts')
    size = len(updates[0]['weights'])
    if any(len(u['weights']) != size for u in updates):
        raise ValueError('Update tensor dimensions differ')
    total = sum(u['num_samples'] for u in updates)
    return [sum(u['num_samples'] * u['weights'][i] for u in updates) / total
            for i in range(size)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clients', default='farm-a,farm-b,farm-c')
    parser.add_argument('--min-quorum', type=int, default=3)
    parser.add_argument('--timeout', type=float, default=8)
    parser.add_argument('--round', type=int, default=1, dest='round_number')
    parser.add_argument('--global-weights', default='0.0')
    parser.add_argument('--output')
    args = parser.parse_args()
    clients = [x.strip() for x in args.clients.split(',') if x.strip()]
    if not clients or not (1 <= args.min_quorum <= len(clients)):
        parser.error('min-quorum must be between 1 and number of clients')
    initial = [float(x) for x in args.global_weights.split(',')]
    if not initial:
        parser.error('global-weights cannot be empty')
    host = os.getenv('RABBITMQ_HOST', 'localhost')
    parameters = pika.ConnectionParameters(host=host, port=int(os.getenv('RABBITMQ_PORT', '5672')))
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange='fl.control', exchange_type='direct', durable=True)
    channel.exchange_declare(exchange='fl.updates', exchange_type='topic', durable=True)
    queue = 'fl.updates.coordinator'
    channel.queue_declare(queue=queue, durable=True)
    channel.queue_bind(exchange='fl.updates', queue=queue, routing_key='fit.*.*')
    channel.confirm_delivery()
    round_id = f"r{args.round_number}-{uuid.uuid4().hex[:10]}"
    for client_id in clients:
        command = {
            'round_id': round_id, 'round': args.round_number,
            'client_id': client_id, 'global_weights': initial,
            'algorithm': 'FedAvg', 'issued_at': time.time(),
        }
        channel.basic_publish(
            exchange='fl.control', routing_key=client_id,
            body=json.dumps(command, separators=(',', ':')).encode(),
            properties=pika.BasicProperties(content_type='application/json', delivery_mode=2,
                                            message_id=f'{round_id}:fit-ins:{client_id}', type='fit_instruction'),
            mandatory=True)
    print(f'[coordinator] dispatched round={round_id} to {clients}', flush=True)
    updates, received = [], set()
    deadline = time.monotonic() + args.timeout
    while len(updates) < args.min_quorum and time.monotonic() < deadline:
        method, properties, body = channel.basic_get(queue=queue, auto_ack=False)
        if method is None:
            time.sleep(0.05)
            continue
        try:
            update = json.loads(body)
            client_id = update['client_id']
            if update.get('round_id') != round_id:
                print(f'[coordinator] discarded stale update from {client_id}', flush=True)
            elif client_id not in clients:
                print(f'[coordinator] discarded unknown client {client_id}', flush=True)
            elif client_id in received:
                print(f'[coordinator] discarded duplicate update from {client_id}', flush=True)
            elif update.get('num_samples', 0) <= 0 or len(update.get('weights', [])) != len(initial):
                print(f'[coordinator] discarded invalid update from {client_id}', flush=True)
            else:
                updates.append(update)
                received.add(client_id)
                print(f'[coordinator] accepted {client_id}: n={update["num_samples"]}', flush=True)
        except (ValueError, KeyError, TypeError) as exc:
            print(f'[coordinator] discarded malformed result: {exc}', flush=True)
        channel.basic_ack(method.delivery_tag)
    if len(updates) < args.min_quorum:
        channel.close()
        connection.close()
        raise SystemExit(f"quorum unavailable: received {len(updates)}/{args.min_quorum} before timeout")
    aggregated = weighted_average(updates)
    result = {
        'round_id': round_id, 'round': args.round_number,
        'algorithm': 'FedAvg', 'participants': sorted(received),
        'received': len(updates), 'expected': len(clients),
        'quorum': args.min_quorum, 'initial_weights': initial,
        'global_weights': aggregated,
        'sample_count': sum(u['num_samples'] for u in updates),
        'status': 'quorum_complete' if len(updates) == len(clients) else 'partial_quorum',
    }
    print('[coordinator] result=' + json.dumps(result, sort_keys=True), flush=True)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as file:
            json.dump(result, file, indent=2)
    channel.close()
    connection.close()


if __name__ == '__main__':
    main()
