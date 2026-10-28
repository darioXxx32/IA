# Workshop 6 â€” Activity 1: RabbitMQ

**Course:** Distributed Systems  
**University:** Yachay Tech University  
**Student:** Dario Pomasqui  
**Date:** 22 October 2026

This folder contains the Activity 1 report, reproducible checks, and screenshots. The original implementations remain in the parent folder.

## Deliverables

- [`reporte-actividad1.md`](reporte-actividad1.md): procedure, test evidence, C/Python comparison, discussion, and limitations.
- The unified Workshop 6 report, including Activity 2, is provided as `../../solution2/reporte-workshop6.pdf` and `../../solution2/reporte-workshop6.tex`.
- [`evidencias/`](evidencias/): captured workshop instructions, RabbitMQ Management UI, test logs, and static inspection results.
- [`ejecutar-pruebas.ps1`](ejecutar-pruebas.ps1): commands used for repeatable Python and broker checks (requires Docker Desktop and Python).

## Run the tests

From PowerShell, in this directory:

```powershell
python -m pip install -r ..\python-basic\requirements.txt
python -m pip install -r ..\python-pubsub\requirements.txt
docker run -d --name workshop6-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ejecutar-pruebas.ps1
```

The script builds a small Ubuntu Docker image that installs `librabbitmq-dev`, compiles both C examples, and tests C producer-to-consumer delivery against the local broker. This avoids the unavailable native Windows library package while preserving the original C sources.

> The Management UI screenshot was captured from the local test broker. The test broker container was left running as `workshop6-rabbitmq`; stop it with `docker stop workshop6-rabbitmq` when finished.

