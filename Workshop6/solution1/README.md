# Activity 1 — RabbitMQ Queue and Fanout Examples

This solution contains the supplied Python and C examples, plus the repeatable setup, tests, and evidence.

## Folder contents

- `python-basic/`: Pika producer and consumer for the durable `hello` queue.
- `python-pubsub/`: Pika publisher and subscriber using the `logs` fanout exchange.
- `c-basic/`: C producer and consumer, with the Makefile.
- `resolucion-actividad1/`: activity report, repeatable PowerShell test script, C build Dockerfile, and `evidencias/`.

## Run

From this folder, install both Python dependency sets and start the broker:

```powershell
python -m pip install -r .\python-basic\requirements.txt
python -m pip install -r .\python-pubsub\requirements.txt
docker run -d --name workshop6-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

Then run the full test script:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\resolucion-actividad1\ejecutar-pruebas.ps1
```

The script checks Python syntax and AMQP connectivity, exercises queue and fanout delivery, builds the C programs in Ubuntu with `librabbitmq-dev`, and tests C producer-to-consumer delivery. It expects Docker Desktop and a broker container named `workshop6-rabbitmq` to be running. If that container already exists but is stopped, start it with `docker start workshop6-rabbitmq`.

The unified report for both activities is in [`../solution2/reporte-workshop6.pdf`](../solution2/reporte-workshop6.pdf).
