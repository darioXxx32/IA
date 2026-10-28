# Report: Message-Oriented Middleware with RabbitMQ

**Workshop 6 — Activity 1**  
**Course:** Distributed Systems, Semester II 2026  
**Institution:** Yachay Tech University  
**Student:** Dario Pomasqui  
**Date:** 22 October 2026

## 1. Objective and scope

The activity asks us to follow the RabbitMQ README, run and discuss tests, and compare the C and Python implementations. The supplied workshop folder contains a Python point-to-point queue, a Python fanout publisher/subscriber pair, and a minimal C queue producer/consumer.

## 2. Environment and setup

The tests were run on Windows with Python 3.13.14, Pika 1.4.4, Docker Desktop 29.2.1, and the `rabbitmq:3-management` image. GCC 13.2.0 was available. Because native Windows `librabbitmq` development packages were unavailable, I installed Ubuntu 24.04 build dependencies into the reproducible `workshop6-c-dev` Docker image using `apt-get install build-essential librabbitmq-dev`. I installed Pika with `python -m pip install pika` and started the broker with:

```powershell
docker run -d --name workshop6-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

AMQP connections use TCP port 5672. The Management UI was available at `http://localhost:15672` on port 15672. Authenticated Management UI screenshots are stored in [`evidencias/rabbitmq-dashboard.png`](evidencias/rabbitmq-dashboard.png) and [`evidencias/rabbitmq-cola-hello.png`](evidencias/rabbitmq-cola-hello.png).

## 3. Procedure and tests

### 3.1 Python queue (point to point)

The consumer declares the durable `hello` queue and sets `prefetch_count=1`. It acknowledges a message after processing it. The producer sends the persistent message `Hello Middleware!` to the default direct exchange using routing key `hello`.

I started the consumer, ran the producer, and checked the broker state with `rabbitmqctl list_queues name messages consumers`.

**Result:** the producer printed `Sent: Hello Middleware!`; RabbitMQ showed queue `hello` with `0` pending messages and one active consumer. The consumer was running and accepted delivery. Its captured terminal output is in [`evidencias/queue-consumer.stdout.txt`](evidencias/queue-consumer.stdout.txt); the broker queue state is visible in [`evidencias/rabbitmq-cola-hello.png`](evidencias/rabbitmq-cola-hello.png).

### 3.2 Python fanout (publish/subscribe)

The supplied publisher declares the durable `logs` fanout exchange and broadcasts without a routing key. Each subscriber creates its own exclusive, server-named queue and binds it to `logs`.

To test broadcast deterministically, I declared two independent exclusive queues, bound both to `logs`, published `Workshop6 fanout test`, and read one delivery from each queue.

**Result:** both queues returned exactly `Workshop6 fanout test`; the assertion passed. The broker confirmed that `logs` is a `fanout` exchange. The exchange screenshot is in [`evidencias/rabbitmq-exchange-logs.png`](evidencias/rabbitmq-exchange-logs.png).

### 3.3 Python syntax and AMQP connectivity

`python -m py_compile` was run on the four Python scripts. A separate Pika connection check opened and closed a connection to `localhost:5672`.

**Result:** all four Python files compiled and AMQP connectivity passed. Static inspection details and file hashes are recorded in [`evidencias/inspection.txt`](evidencias/inspection.txt).

### 3.4 C producer/consumer

The README builds these examples with `make`, linking `librabbitmq` (`-lrabbitmq`). The original C examples were built inside an Ubuntu 24.04 Docker image with `build-essential` and `librabbitmq-dev` installed. I added environment-based broker host selection (`RABBITMQ_HOST`) and checks for login, channel setup, queue declaration, and publish errors.

**Result:** `make` compiled both C programs successfully. I started the C consumer in a container and published `Hello from C!` using the C producer; the consumer printed the received message and acknowledged it. Captured output: [`evidencias/activity1-c-consumer.txt`](evidencias/activity1-c-consumer.txt).

## 4. Test summary

| Check | Result | Observation |
|---|---|---|
| Broker available on AMQP | PASS | Pika connected to `localhost:5672`. |
| Python queue producer | PASS | `Hello Middleware!` published to `hello`; queue had no pending messages while its consumer was connected. |
| Fanout broadcast | PASS | Two separately bound subscriber queues received the same test message. |
| Python syntax | PASS | Four Python programs compiled with `py_compile`. |
| C build/runtime | PASS | Compiled both programs in Ubuntu with `librabbitmq-dev`; C producer-to-consumer delivery succeeded. |

## 5. C and Python comparison

| Aspect | Python (`pika`) | C (`rabbitmq-c`) |
|---|---|---|
| API and code | BlockingConnection and callbacks make the example compact and easy to read. | Explicit connection, socket, channel, byte buffer, and envelope management expose more AMQP details. |
| Dependencies | Python interpreter and Pika package. | C compiler plus rabbitmq-c development headers and linker library. |
| Delivery behavior | Queue is durable; producer marks the message persistent; consumer uses prefetch 1 and explicitly acknowledges after processing. | Producer marks its message persistent; consumer explicitly acknowledges each envelope. The C queue declaration is durable. |
| Error handling in supplied sample | Pika raises exceptions on connection/protocol errors; the minimal sample does not add retries. | The sample checks socket creation/opening and consume replies, but assumes login/channel/declare/publish succeed in places. It is intentionally minimal. |
| Best fit | Rapid implementation, experimentation, and integration with Python ML services. | Native systems and deployments where a C ABI, low-level control, or integration with existing C software is required. |

Both clients use the same AMQP broker and queue model, so the middleware semantics are not language-specific. Python has a lower setup and code-complexity cost for this lab. C gives explicit resource and protocol control but requires native dependencies and stronger error checks for production use.

## 6. Discussion

The queue example provides work distribution: one message enters `hello`, and a competing consumer handles it. Manual acknowledgement lets RabbitMQ requeue unacknowledged deliveries if a consumer disconnects. Durability and persistent delivery improve restart survival, but do not by themselves guarantee end-to-end exactly-once processing; a consumer can perform an operation and fail before acknowledging it, so applications should make processing idempotent where duplicate deliveries matter.

The fanout example provides broadcast: every subscriber with a bound queue gets a copy while that queue exists. The supplied subscriber uses an exclusive, auto-deleted queue, so messages published while it is offline are not retained for that subscriber. This behavior is appropriate for transient live logs, but durable subscriptions would need named durable queues and suitable message persistence.

RabbitMQ decouples producers from consumers in time and process location, offers routing, acknowledgements, and buffering, and supports clients in both C and Python. It is therefore a useful message-oriented middleware for distributed components. Python is the easier implementation to reproduce natively on the host; C also ran successfully after installing its development package in the Ubuntu Docker build image.

## 7. Evidence and reproducibility

The [`evidencias`](evidencias/) folder contains the assignment first page, authenticated Management UI screenshots, Python and C consumer output, and static inspection results. [`ejecutar-pruebas.ps1`](ejecutar-pruebas.ps1) reruns the Python checks and exercises the queue producer and two-subscriber fanout against the local broker. The repeatable script builds the Ubuntu image, installs `librabbitmq-dev`, compiles the C programs, and verifies C producer-to-consumer delivery.

The local Docker container `workshop6-rabbitmq` was left running for review. Stop it with `docker stop workshop6-rabbitmq` when finished.
