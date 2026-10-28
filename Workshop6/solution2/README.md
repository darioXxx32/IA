# Activity 2 — RabbitMQ Federated Learning Prototype

This solution contains my RabbitMQ prototype for communication between a coordinator and three farm clients. It models the distributed message flow and weighted FedAvg aggregation with synthetic scalar updates; it does not train a CNN or load PlantVillage.

## Contents

- `coordinator.py` and `client.py`: coordinator and farm worker processes.
- `run_demo.py`: launches a complete round or a partial-quorum/dropout scenario.
- `test_protocol.py`: unit tests for aggregation validation.
- `protocolo.md`: exchanges, queues, message fields, failure behavior, rationale, and limitations.
- `result.json` and `result-dropout.json`: sample complete-round and partial-quorum outputs.
- `evidencias/`: test logs and RabbitMQ Management screenshots.
- `figures/`: university logos used by the combined report.
- `reporte-workshop6.pdf` and `reporte-workshop6.tex`: combined report for both activities.

## Run

Run these commands from the project repository root. Start the local RabbitMQ broker first, then install the dependency and run the demo:

```powershell
docker start workshop6-rabbitmq
python -m pip install -r Workshop6/solution2/requirements.txt
python Workshop6/solution2/run_demo.py
```

The complete round should produce a weighted FedAvg value of approximately `2.833333`. To simulate Farm C being offline, run:

```powershell
python Workshop6/solution2/run_demo.py --dropout farm-c
```

The partial-quorum run should produce approximately `1.666667` and leave Farm C's instruction in its durable queue. For the protocol design and limitations, see [`protocolo.md`](protocolo.md). The project proposal is at `../../proporsal/proposal.tex`.
