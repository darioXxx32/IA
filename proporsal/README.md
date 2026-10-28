# Federated Crop Disease Detection Proposal

> **Project:** *Evaluating FedAvg and FedProx for Federated Crop Disease Detection under Data Heterogeneity*  
> **Author:** Dario Pomasqui  
> **Institution:** Yachay Tech University  
> **Course context:** Distributed Systems

This folder contains the written project proposal, its presentation, and a speaker script. The proposal frames crop disease classification as a **distributed systems and federated learning** problem: multiple farms collaborate on a shared model while keeping their raw images on their own nodes.

## Contents

- [Project at a glance](#at-a-glance)
- [Why this is a distributed systems project](#why-this-is-a-distributed-systems-project)
- [Farm-node state](#what-state-does-a-farm-node-keep)
- [Round lifecycle and RabbitMQ messages](#round-lifecycle-and-messages)
- [FedAvg and FedProx](#algorithms-under-study)
- [Data and evaluation plan](#data-heterogeneity-and-evaluation-plan)
- [Folder and file guide](#files-in-this-folder)
- [How to compile](#compile-the-documents)
- [Reproduction and interpretation notes](#reproduction-and-interpretation-notes)

---

## At a glance

- **Problem:** Farm datasets differ in disease prevalence, environment, and imaging conditions. This non-IID data can make local model updates pull in different directions (client drift).
- **Participants:** Three simulated farm clients and one logical coordinator.
- **Algorithms:** FedAvg as the baseline and FedProx as the method under study.
- **Communication middleware:** RabbitMQ using AMQP 0-9-1, for brokered coordinator-to-client messaging.
- **Data basis:** PlantVillage, partitioned into controlled IID and non-IID distributions.
- **Evaluation themes:** Classification quality, minority-class recall, round-to-round stability, communication cost, and behavior when a client drops out.

The proposal describes the research design and records preliminary protocol-level validation. It should not be mistaken for a complete production deployment or a claim that full-scale CNN experiments have all been completed. Check the current implementation and results before treating any stated measurement as a final research result.

## Why this is a distributed systems project

The farms are modeled as independent compute nodes. Each has private data, local model state, and its own processing lifecycle. Nodes train locally and communicate serialized instructions and updates through a message broker. The coordinator controls model versions and aggregation rounds; it does not receive raw farm images.

RabbitMQ is the **message-oriented middleware** in this design. It is a broker service implementing AMQP; it is not itself the federated learning algorithm, and it is not a Python library or a Docker container. It can be run directly or as a container, while Python clients connect to it using a client library such as `pika` (the current `requirements.txt` does not list `pika`).

The architecture is a **hub-and-spoke coordinator/worker design**:

```text
                         ┌────────────────────┐
                         │  Global coordinator│
                         │ FedAvg / FedProx    │
                         │ round orchestration│
                         └─────────┬──────────┘
                                   │
                            RabbitMQ / AMQP
                         ┌─────────┴──────────┐
                         │                    │
                 ┌───────┴──────┐     ┌───────┴──────┐     ┌──────────────┐
                 │ Farm A worker│     │ Farm B worker│ ... │ Farm C worker│
                 │ private data │     │ private data │     │ private data │
                 └──────────────┘     └──────────────┘     └──────────────┘
```

The diagram in the proposal gives the full data flow, including the dataset partitioning stage and evaluation/edge-support outputs.

## What state does a farm node keep?

The proposal uses this tuple to summarize the local state of participant `k`:

\[
\sigma_k = (w_k, \mathcal{D}_k, n_k, t_k)
\]

| Symbol | Meaning |
|---|---|
| `w_k` | The model parameters currently held by farm `k`. At the beginning of a round, the worker synchronizes these with the global parameters it receives. |
| `D_k` | The farm's private local dataset (or its local partition of the benchmark in the simulation). Raw images stay at the worker. |
| `n_k` | Number of local training samples represented by that worker's update; used to weight aggregation. |
| `t_k` | The local round/version index known to the worker. It helps associate work with a federated round. |

This tuple is a **mathematical description of node state**, not a requirement that the software store these four values in one literal tuple object. It also does not mean the full dataset is sent in messages.

## Round lifecycle and messages

The proposal describes a round as the following sequence:

1. The coordinator publishes a `FitIns` instruction containing round/version information and the current global model parameters.
2. RabbitMQ routes the instruction to the appropriate durable worker command queue.
3. Each available farm synchronizes its local model, trains on its own data, and forms an update.
4. The worker publishes a `FitRes` containing its updated parameters, sample count, round identifier, and relevant metrics.
5. The coordinator validates and de-duplicates responses, then waits at a barrier until the configured quorum is met or a timeout expires.
6. The coordinator aggregates the available updates and assigns the next global model version.
7. A worker that was offline can catch up by receiving a later model version when it rejoins.

The proposal names a direct exchange for downlink control messages (`fl.control`) and a topic exchange for uplink results (`fl.updates`). These names and delivery properties are part of the design described in the document; verify the current implementation configuration before using them as deployment instructions.

### What the quorum does—and does not—mean

A minimum participant count lets the coordinator proceed after a worker dropout instead of waiting forever. It is an application-level barrier policy. It is **not** a consensus protocol such as Raft or Paxos and does not by itself provide replicated coordinator state, split-brain protection during coordinator failure, or a proof that the responding sample is statistically representative. The proposal explicitly treats those as design boundaries.

## Algorithms under study

### FedAvg

Each worker performs local training, then the coordinator computes a sample-weighted average:

\[
w^{(t+1)} = \sum_{k \in \mathcal{S}_t}
\frac{n_k}{\sum_{j \in \mathcal{S}_t}n_j}w_k^{(t+1)}.
\]

Here, \(\mathcal{S}_t\) is the set of workers whose updates are accepted for round `t`. If a client drops out and the minimum quorum is still satisfied, weights are normalized over the responding workers.

### FedProx

FedProx changes the **local training objective** by adding a proximal penalty centered on the current global model:

\[
F_k(w) + \frac{\mu}{2}\lVert w-w^{(t)}\rVert_2^2.
\]

The penalty discourages a worker's local model from moving too far from the round's global starting point. The proposal investigates multiple values of `μ` and compares the resulting training behavior with FedAvg. The coordinator's weighted aggregation remains structurally similar; the main algorithmic difference is the local objective.

## Data heterogeneity and evaluation plan

PlantVillage is used as the public plant pathology benchmark described by the proposal. The data is partitioned across three simulated farms to study:

- **IID:** approximately similar class distributions across clients.
- **Non-IID:** client distributions sampled with Dirichlet controls and/or constructed to represent localized disease patterns.
- **Client dropout:** a worker fails to respond during a round, exercising timeout and quorum handling.

The proposed measures include classification accuracy, macro-F1, minority-disease recall, inter-round stability, client-update divergence, communication cost, and round/barrier latency. A small gradient norm or a successful aggregation alone does not establish good diagnostic generalization; metrics and experiment conditions need to be reported together.

## Files in this folder

| Path | Purpose |
|---|---|
| `proposal.tex` | Main research proposal, currently formatted with the official MDPI LaTeX class. It contains the research question, related work, distributed design, methods, preliminary prototype discussion, work plan, declarations, and references. |
| `proposal.pdf` | Compiled PDF of `proposal.tex`. Recompile it after editing the source. |
| `Definitions/` | MDPI class, bibliography styles, journal metadata, and logo assets required by the source. Keep this directory beside `proposal.tex`. |
| `presentacion.tex` | Beamer slide deck covering the motivation, algorithms, node lifecycle, RabbitMQ architecture, preliminary validation, plan, and expected contributions. |
| `presentacion.pdf` | Compiled slide deck. |
| `speach/speach.tex` | Detailed speaker script aligned to the slide sequence. The folder name is kept as it currently exists in the project. |
| `speach/speach.pdf` | PDF rendering of the speaker script. |
| `imagenes/logo1.png`, `imagenes/logo2.png` | Local image assets available to project documents. |
| `requirements.txt` | Python packages listed for the planned/related federated learning implementation: Flower, PyTorch, torchvision, NumPy, and Matplotlib. These do not install RabbitMQ or LaTeX. |
| `*.aux`, `*.log`, `*.nav`, `*.toc`, `*.fls`, etc. | LaTeX build byproducts. They are not source files; they can be regenerated by the relevant LaTeX tool. |

The proposal's main architecture figure is drawn directly with TikZ in `proposal.tex`, so it does not depend on an external diagram image.

## Compile the documents

Run commands from this directory so relative paths such as `Definitions/mdpi` resolve correctly. Install a LaTeX distribution (MiKTeX or TeX Live) with the packages used by MDPI, TikZ/PGFPlots, Beamer, and `listings` available.

### Proposal

```powershell
cd C:\Users\User\Desktop\8vo\Sistemas-Distribuidos\Proyect-Machine-Distributed\proporsal
pdflatex -interaction=nonstopmode -halt-on-error proposal.tex
pdflatex -interaction=nonstopmode -halt-on-error proposal.tex
```

Run LaTeX twice so citations, labels, and page references settle. The official MDPI class is local under `Definitions/`; it is not fetched automatically from the network during compilation.

### Presentation

```powershell
pdflatex -interaction=nonstopmode -halt-on-error presentacion.tex
pdflatex -interaction=nonstopmode -halt-on-error presentacion.tex
```

### Speaker script

```powershell
cd speach
pdflatex -interaction=nonstopmode -halt-on-error speach.tex
pdflatex -interaction=nonstopmode -halt-on-error speach.tex
```

The Python `requirements.txt` is for Python code, not for compiling these PDFs. From the proposal folder it can be installed with:

```powershell
python -m pip install -r requirements.txt
```

That command installs Python packages only. It does not start an AMQP broker or create the client/coordinator application.

## Reproduction and interpretation notes

- Keep the proposal source, the `Definitions/` directory, and any referenced local assets together when copying or archiving this folder.
- Make edits in `.tex` files; PDFs and auxiliary files should be regenerated from those sources.
- Record the exact code version, broker configuration, dataset partition seed, client count, hyperparameters, and test command alongside any new experimental result.
- Clearly label results as **simulated**, **preliminary**, or **full training** as appropriate. Do not present a proposed experiment as completed evidence.
- A durable RabbitMQ queue can retain a message for later consumption when configured correctly; it does not guarantee that model training is correct or that an offline client automatically resumes without application logic.
- The benchmark partitions model statistical heterogeneity. They do not reproduce every operational difference between real farms, networks, cameras, or growing conditions.
- Before submission, check that citations, external repository links, and any claimed test outputs are current and accessible.

## References behind the design

The proposal's bibliography includes the foundational FedAvg paper by McMahan et al., the FedProx work by Li et al., the PlantVillage disease-classification work by Mohanty et al., and distributed-systems references. Consult the bibliography at the end of `proposal.tex` for the complete entries and cited literature.

---

**Maintainer note:** Treat this README as a map to the current proposal materials. For authoritative project status, use the latest source code, test reports, and experiment outputs rather than relying on prose in a proposal or presentation.
