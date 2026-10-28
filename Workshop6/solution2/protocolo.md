# RabbitMQ protocol and distributed architecture

## Project context

The project compares FedAvg and FedProx across three autonomous farm clients holding non-IID foliar image partitions. Images stay at the farm. A coordinator controls rounds, collects parameter updates, computes the weighted global model, records metrics, and sends the next model to the farms.

## Topology and middleware

Use a hub-and-spoke topology with RabbitMQ as the AMQP 0-9-1 message broker. The coordinator is the logical single writer for round state and aggregated model versions. Each farm is an independent worker process with private data and compute. The broker is a routing and buffering service, not the owner of training state.

| Flow | Exchange / queue | Pattern |
|---|---|---|
| Coordinator → farms | durable direct exchange `fl.control`; one durable queue `fl.command.<farm_id>` per farm | Route one model/version and fit instruction to each farm key. |
| Farms → coordinator | durable topic exchange `fl.updates`; coordinator queue `fl.updates.coordinator` bound to `fit.*.*` | Route `FitRes` results tagged by round and farm. |
| Coordinator → metrics / observers (future) | topic exchange `fl.events`, bindings such as `round.*.complete` | Asynchronous status and monitoring events. |

## Round state machine

`COLLECTING(t, model_version=t)` → route an individual `FitIns(t)` to each farm → farms install the exact global model version, train locally, and publish `FitRes(t, client_id, n_k, weights, metrics)` → coordinator validates round/client/schema and de-duplicates `(t, client_id)` → wait for quorum or deadline → calculate sample-weighted FedAvg over accepted clients → persist model version `t+1` → publish the next instruction.

The prototype uses a per-farm coordinator command per round and three independent client processes. The simulator's local update deltas stand in for trained tensors. The full production protocol carries serialized tensors, model hashes, dataset version, algorithm configuration, and metric summaries.

## Message envelope

AMQP properties carry `content_type=application/json`, `delivery_mode=2`, unique `message_id`, `correlation_id=round_id`, and typed messages (`fit_instruction`, `fit_result`). The JSON payload carries a schema version, run ID, logical round, client ID, model version/hash, sample count, weights or tensor artifact reference, and metrics. Large tensors should be stored as compressed binary artifacts or chunked payloads; JSON/base64 is not suitable for large CNNs.

## Delivery, consistency, and failure handling

- Durable queues and persistent messages allow queued work to survive broker restart, subject to broker disk persistence and publisher confirms.
- Consumers use manual acknowledgements. A farm acknowledges a command only after its result is accepted by the broker. A coordinator acknowledges each result after validation/recording.
- AMQP delivery is at-least-once in failure cases. Application de-duplication on `(run_id, round, client_id)` prevents a redelivered update from being counted twice; it does not create a general exactly-once transaction across model storage and the broker.
- Every result is fenced by the logical round and model version. Late responses from an expired round are acknowledged and discarded.
- A configurable deadline distinguishes unavailable/slow farms. The coordinator may aggregate only after `min_quorum` unique updates arrive. It normalizes sample weights over that responsive set; if quorum fails, it aborts the round and retains the prior model.
- The coordinator is a single logical writer. A production deployment needs durable coordinator checkpoints and leader election/fencing (or an externally managed single active replica) before allowing coordinator failover. Replicating only the broker does not prevent split-brain model versions.

## Rationale and trade-offs

RabbitMQ fits intermittent farm connectivity because durable queues buffer commands and results while endpoints recover, and it separates local training time from coordinator network sessions. Direct and topic routing naturally express per-farm downlink instructions and uplink result collection. AMQP clients exist in both C (`rabbitmq-c`) and Python (`pika`), which directly supports the workshop comparison and the project's Python implementation. The hub remains a coordinator bottleneck and a security boundary; TLS, per-farm credentials/vhosts, resource limits, payload validation, encrypted storage, and model update privacy protections are required before deployment. RabbitMQ does not make FL Byzantine-resilient or provide secure aggregation by itself.
