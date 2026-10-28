"""Launch three isolated farm processes and the coordinator for one local round."""
import os
import subprocess
import sys
import time
from pathlib import Path
import argparse
import pika

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--dropout', choices=('farm-a', 'farm-b', 'farm-c'))
parser.add_argument('--min-quorum', type=int)
args = parser.parse_args()
env = os.environ.copy()
env.setdefault('RABBITMQ_HOST', 'localhost')
env.setdefault('RABBITMQ_PORT', '5672')
farm_specs = [
    ('farm-a', 10, 1.0),
    ('farm-b', 20, 2.0),
    ('farm-c', 30, 4.0),
]
processes = []
active_farms = [x for x in farm_specs if x[0] != args.dropout]
min_quorum = args.min_quorum or (2 if args.dropout else 3)
if not (1 <= min_quorum <= len(active_farms)):
    parser.error('min-quorum must be between 1 and the number of active farms')
try:
    # This is an isolated, repeatable smoke test. Clear durable leftovers from prior runs.
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=env['RABBITMQ_HOST'], port=int(env['RABBITMQ_PORT'])))
    channel = connection.channel()
    for queue in ('fl.command.farm-a', 'fl.command.farm-b',
                  'fl.command.farm-c', 'fl.updates.coordinator'):
        channel.queue_declare(queue=queue, durable=True)
        channel.queue_delete(queue=queue, if_unused=False, if_empty=False)
    try:
        channel.exchange_declare(exchange='fl.control', exchange_type='direct', durable=True)
    except pika.exceptions.ChannelClosedByBroker as error:
        if error.reply_code != 406:
            raise
        # Recover a stale prototype exchange created with a different type.
        channel = connection.channel()
        channel.exchange_delete(exchange='fl.control', if_unused=False)
        channel.exchange_declare(exchange='fl.control', exchange_type='direct', durable=True)
    for client_id, _, _ in farm_specs:
        queue = f'fl.command.{client_id}'
        channel.queue_declare(queue=queue, durable=True)
        channel.queue_bind(exchange='fl.control', queue=queue, routing_key=client_id)
    channel.close()
    connection.close()
    for client_id, samples, delta in active_farms:
        processes.append(subprocess.Popen([
            sys.executable, '-u', str(ROOT / 'client.py'), '--id', client_id,
            '--samples', str(samples), '--delta', str(delta)],
            cwd=ROOT, env=env, stdout=None, stderr=None))
    time.sleep(1.5)
    subprocess.run([
        sys.executable, '-u', str(ROOT / 'coordinator.py'), '--round', '1',
        '--clients', ','.join(x[0] for x in farm_specs), '--min-quorum', str(min_quorum),
        '--timeout', '3' if args.dropout else '10',
        '--output', str(ROOT / ('result-dropout.json' if args.dropout else 'result.json'))],
        cwd=ROOT, env=env, check=True)
finally:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
