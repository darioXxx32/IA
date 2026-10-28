# Federated Crop Disease Detection
## Project guide and presentation notes

**Project title:** *Evaluating FedAvg and FedProx for Federated Crop Disease Detection under Data Heterogeneity*  
**Author:** Dario Pomasqui  
**Institution:** Yachay Tech University  
**Course:** Distributed Systems

This README is a written companion to [`presentacion.tex`](presentacion.tex). It follows the story of the slides: why farms need a distributed solution, how the farm nodes communicate, what FedAvg and FedProx do, how the experiments are organized, and what the current prototype results mean. Formulas are written as plain text/code so they remain readable in GitHub and other Markdown viewers.

> **Project status:** This folder contains a proposal, presentation, and speaker script. The proposal reports preliminary middleware/protocol validation and describes further federated CNN experiments as work in progress or planned. Treat each result according to the status stated in the source and verify it against the current code and test artifacts before presenting it as final evidence.

## Contents

- [The story in one minute](#the-story-in-one-minute)
- [Presentation walkthrough](#presentation-walkthrough)
- [How the distributed design works](#how-the-distributed-design-works)
- [The math without rendering problems](#the-math-without-rendering-problems)
- [Experiments and what they test](#experiments-and-what-they-test)
- [Files in this folder](#files-in-this-folder)
- [Compile the LaTeX documents](#compile-the-latex-documents)
- [Terminology and interpretation notes](#terminology-and-interpretation-notes)

## The story in one minute

Different farms see different crop diseases and use different cameras and growing conditions. Their image collections are therefore not identically distributed. If the farms upload all photographs to one central repository, they give up control of sensitive data and need enough network capacity to transfer it.

Federated learning lets each farm train locally and send model updates to a coordinator. The project compares two ways to combine that work: **FedAvg**, which averages client models weighted by each client's sample count, and **FedProx**, which adds a penalty to local training to discourage a client from drifting too far from the current global model. **RabbitMQ** carries coordinator/worker messages; it is the communication middleware, not the learning algorithm. A simulated three-farm system is used to study data heterogeneity, message flow, synchronization, and a worker dropout scenario.

## Presentation walkthrough

This section follows the narrative of `presentacion.tex` and expands each idea into plain language.

### 1. Title and project scope

The project asks whether FedProx can improve crop disease classification when independent farm nodes have different local data. It combines a distributed coordinator/worker design with federated optimization. The agricultural network is simulated; the proposal does not claim that the experiment represents a deployment across real farms.

### 2. Why agriculture needs collaboration

Crop disease recognition can benefit from models trained on varied leaf images. But each producer owns a different subset of that information. Sending all photographs to one central service can raise privacy, commercial confidentiality, storage, and rural connectivity concerns. Federated learning aims to share model improvements while keeping the raw images at each participant.

### 3. Non-IID data and client drift

“Non-IID” means that clients do not have matching data distributions. For example, one simulated farm can have more rust and blight, another more bacterial spots or mildew, and a third more viral or healthy leaves. Differences in lighting, backgrounds, and camera sensors add further variation.

Because each worker trains on its own data, its local model can move toward patterns that are common at that farm. Those local directions may disagree with the global objective. This divergence is called **client drift**. It can make simple averaging unstable and can hurt classes that are rare on some clients. The experiments test this concern; they do not assume that one optimizer must always win.

### 4. Research question and hypotheses

The central question is whether FedProx improves diagnostic performance, stability across rounds, and generalization across clients compared with FedAvg when farm data is non-IID.

The proposal's hypotheses are:

1. Under IID data, FedAvg and FedProx may perform similarly; under stronger skew, FedProx may better preserve macro-F1 and minority-class recall.
2. FedProx's proximal penalty may reduce round-to-round performance oscillations.
3. A middle-range value of `mu` may balance client stability against overly restricted local training.
4. Under a client dropout scenario, FedProx may retain more stable model updates.

These are hypotheses to evaluate, not results guaranteed by the design.

### 5–6. Distributed coordination and round latency

The system has one logical coordinator and several workers. For each round the coordinator sends the current model, clients train, clients return updates, and the coordinator aggregates accepted responses. The round behaves like a barrier: it cannot complete until the required client responses arrive or the timeout/quorum rule allows it to proceed.

The latency model in the slides can be read as:

```text
round_time = slowest_client(downlink_time + local_compute_time + uplink_time)
             + aggregation_time
```

The slowest participating client is a **straggler** and can dominate the round time. More local computation or slower links can reduce overall throughput. The project also tracks the size of serialized model updates because sending parameters is intended to cost less network bandwidth than sending all original images. Any claimed percentage reduction depends on the model size and image volume used in the actual experiment.

### 7. What each farm node contains

Each farm is modeled as an autonomous node with private storage, its own compute, and a local copy of the model. Nodes do not share memory or a filesystem; they exchange messages over the broker.

The presentation summarizes node `k` with this state tuple:

```text
sigma_k = (w_k, D_k, n_k, t_k)
```

- `w_k`: current local model parameters.
- `D_k`: the farm's private dataset, or that farm's assigned benchmark partition in the simulation.
- `n_k`: the number of training examples represented by the client's update.
- `t_k`: the local federated round/model version known to that worker.

This is a mathematical way to describe local state. The program does not have to store these fields in one literal tuple. The dataset stays at the client; it is not included in the update message.

### 8. Worker lifecycle and dropout handling

A worker proceeds through the following states:

```text
IDLE -> SYNCHRONIZING -> TRAINING -> REPORTING
  \                                      /
   +------------ PARTITIONED ------------+
```

- **IDLE:** waiting for a training instruction.
- **SYNCHRONIZING:** installs the global model version for the new round.
- **TRAINING:** performs local epochs on private data.
- **REPORTING:** returns the model update and sample count.
- **PARTITIONED:** cannot communicate before the timeout; the coordinator decides whether the current round can continue with the available clients.

When a disconnected worker returns, it can synchronize with a later global model version. This is called **state catch-up** in the presentation. It requires the client application to consume and install that version; a durable queue alone does not perform model recovery.

### 9. Architecture and message flow

The architecture has three farm workers, a RabbitMQ broker, a coordinator, and evaluation/edge-support components:

```text
PlantVillage images
        |
        v
controlled IID / non-IID partitioning
        |
        +--> Farm A worker -- FitRes --+
        +--> Farm B worker -- FitRes --+--> RabbitMQ --> Coordinator
        +--> Farm C worker -- FitRes --+                    |
              ^                         <--- FitIns --------+
              |
       private local training                       global model
                                                        |
                                    +-------------------+-------------------+
                                    v                                       v
                              edge support                         evaluation
```

The proposal describes `FitIns` as a downlink instruction (round information and global weights) and `FitRes` as an uplink response (updated weights, sample count, and metrics). RabbitMQ routes messages between workers and coordinator. Raw images remain in each worker's local data partition.

### 10. Data partitions and the farmer support tool

The presentation proposes four data regimes to vary the degree of heterogeneity:

- **IID:** clients have approximately balanced class distributions.
- **Low non-IID:** a Dirichlet partition with `alpha = 1.0` creates mild variation.
- **Medium non-IID:** `alpha = 0.5` creates more concentrated class distributions.
- **High non-IID/disjoint:** each farm receives a dominant disease cluster and fewer examples from the others.

The exact implementation should document the partition seed, partition method, and actual class counts. A proposed edge tool would run an exported model on a leaf image and return a disease prediction with a confidence score. The presentation mentions calibration (for example, temperature scaling and expected calibration error) because a high softmax score is not automatically a reliable probability. Agronomic treatment advice is a future product feature and should not be confused with a validated medical/agronomic recommendation.

### 11. Six experimental tracks

The slide deck organizes the evaluation into six tracks:

1. Compare FedAvg and FedProx on global performance and convergence.
2. Measure the effect of increasingly non-IID partitions.
3. Sweep the FedProx penalty `mu` across `0.001`, `0.01`, `0.1`, and `1.0`.
4. Disconnect a worker during training and assess the round protocol.
5. Measure serialized communication size and round/barrier latency.
6. Measure per-client performance and recall for minority disease classes.

A stability metric in the slides is the sample standard deviation of the round-to-round accuracy changes:

```text
S_delta_acc = standard_deviation(delta_acc_2, ..., delta_acc_R)
```

Lower values indicate less variation in those accuracy changes for the measured run. They do not by themselves prove better final accuracy or convergence.

### 12. Preliminary RabbitMQ prototype results

The slides and proposal report a protocol-level prototype comparison using synthetic updates:

| Scenario | Responding clients | Samples | Reported aggregate | Reported barrier behavior |
|---|---:|---:|---:|---|
| Complete round | 3 of 3 | 60 | 2.8333 | about 120 ms; queues drained and acknowledgments confirmed |
| Farm C dropout | 2 of 3 | 30 | 1.6667 | 3 s timeout; coordinator proceeds with the surviving clients |

For the complete round, the illustrative weighted arithmetic is:

```text
(10 * 1 + 20 * 2 + 30 * 4) / (10 + 20 + 30)
= 170 / 60
= 2.8333
```

For the dropout round with only A and B:

```text
(10 * 1 + 20 * 2) / (10 + 20)
= 50 / 30
= 1.6667
```

These values illustrate message handling and weighted aggregation with synthetic client updates. They are not CNN accuracy results and do not establish how FedAvg/FedProx perform on PlantVillage. Timing figures should be reported with the exact test setup and source output that produced them.

### 13. Distributed systems concepts

The design applies message passing, round identifiers, timeouts, duplicate suppression, and weighted aggregation. A message's causal order is described as:

```text
broadcast instruction -> local training -> upload result -> aggregation
```

Round and client identifiers let the coordinator reject duplicate results. A single logical writer assigns global model versions, avoiding independent workers committing separate versions while that coordinator is healthy. The proposal does not replicate the coordinator or supply coordinator failover.

The slides use CAP terminology to discuss availability and network partitions. Read this as a design discussion, not a formal CAP proof: the coordinator/barrier still constrains whether a global round can advance, and local training while disconnected is not the same as committing a globally consistent model.

### 14. Software deliverables and edge deployment

The proposed software pipeline separates:

- federated training simulation (Python, PyTorch, Flower/RabbitMQ components as implemented),
- dataset partitioning and evaluation,
- model export (the slides mention ONNX or TorchScript), and
- a lightweight C++ edge inference runtime.

The C++ runtime and sub-50-ms inference figure are planned targets in the presentation, not outputs demonstrated by the current proposal PDF. Confirm the implementation and measured device before claiming them as completed.

### 15–16. Schedule, reproducibility, and final report

The deck lays out six phases, from the message-middleware prototype and data partitioning through CNN training, benchmark tracks, edge export, and final analysis. It lists some early phases as completed, CNN integration as in progress, and later phases as planned. Keep these status labels current as the project changes.

For repeatable experiments, record at least the source revision, dataset/partition configuration, random seed, client count, algorithm and hyperparameters, broker settings, timeout/quorum, test command, and generated results. The final report should distinguish protocol verification from model-performance evaluation and should include plots/tables generated from the current result files.

### 17. Conclusion

The expected contribution is a controlled study connecting federated optimization with distributed-system behavior in a crop-disease setting. The main question is not simply which algorithm gets the highest score; it is how data skew, local optimization, message timing, and worker availability affect the quality and stability of the shared model.

## How the distributed design works

### Middleware: RabbitMQ

RabbitMQ is a message broker implementing AMQP. It is a service/process (and can be containerized); it is not a Python library and is not the federated learning algorithm. Python workers use a client library to connect to it. The current [`requirements.txt`](requirements.txt) contains `flwr`, `torch`, `torchvision`, `numpy`, and `matplotlib`, but does **not** list `pika` or install/start a RabbitMQ server.

The proposal names two logical message paths:

| Direction | Message | Purpose |
|---|---|---|
| Coordinator to workers | `FitIns` | Round/version and global model parameters for local training. |
| Workers to coordinator | `FitRes` | Updated parameters, sample count, round identifier, and metrics. |

The proposal uses a durable direct route for commands and topic routing for results. Verify exact exchange names, persistence settings, publisher confirmation, acknowledgments, and retry behavior against the source code before using them as an operational setup guide.

### Quorum and system boundaries

A minimum quorum is an application rule that says whether the coordinator has enough responses to process a round. A timeout bounds how long it waits. If a worker is absent, the coordinator can re-normalize sample weights over the responding set if the configured minimum is met.

This mechanism does not make RabbitMQ a consensus service. It does not automatically provide majority consensus, replicated coordinator state, split-brain prevention during coordinator failure, or Byzantine fault tolerance. The proposal assumes fail-stop workers for its dropout experiment; malicious or corrupted updates require separate mechanisms.

## The math without rendering problems

The expressions below are intentionally plain text rather than LaTeX, so a Markdown viewer will display them without exposing TeX commands.

### FedAvg aggregation

```text
w_global_next = sum over participating clients k of:
                (n_k / sum of n_j for participating clients) * w_k_next
```

Each client contributes in proportion to its number of local examples. `w_k_next` is the model after client `k` trains for the current round.

### FedProx local objective

```text
local_objective_k(w) = F_k(w) + (mu / 2) * ||w - w_global_current||^2
```

`F_k(w)` is the farm's local training loss. `mu` controls the strength of the penalty. The penalty is zero at the round's starting global model and grows as the local model moves away from it.

### Round time

```text
round_time = max over participating clients k of:
             (downlink_k + local_compute_k + uplink_k)
             + aggregation_time
```

This model makes the straggler effect visible: with a full barrier, a slow participant can determine the round duration.

### Local-state tuple

```text
sigma_k = (w_k, D_k, n_k, t_k)
```

This summarizes the local model, local dataset, local sample count, and known round/version. It is descriptive notation; it need not be one literal Python tuple.

## Experiments and what they test

| Experiment dimension | What changes | What to report |
|---|---|---|
| Algorithm | FedAvg or FedProx | global accuracy/loss and round count |
| Data distribution | IID through stronger non-IID skew | partition details, client class counts, macro-F1 and per-class recall |
| FedProx setting | `mu` penalty value | performance and stability for each declared value |
| Availability | a client drops out at a specified round | timeout, accepted quorum, resulting aggregation and recovery behavior |
| Communication | update size and message timing | payload per round, barrier latency, aggregation time, environment |

A robust report should include multiple runs or explain why deterministic results do not need statistical replication, preserve raw output files, and avoid drawing broad conclusions from one synthetic protocol test.

## Files in this folder

| Path | Purpose |
|---|---|
| [`proposal.tex`](proposal.tex) | Main research proposal; uses MDPI class, describes the research design, architecture, experiments, preliminary protocol validation, schedule, and bibliography. |
| [`proposal.pdf`](proposal.pdf) | Compiled proposal PDF. Rebuild after editing the TeX source. |
| [`Definitions/`](Definitions/) | Local MDPI class, bibliography styles, journal metadata, and logos required to compile the proposal. Keep it beside `proposal.tex`. |
| [`presentacion.tex`](presentacion.tex) | 17-slide Beamer presentation that this README follows. |
| [`presentacion.pdf`](presentacion.pdf) | Compiled slide deck. |
| [`speach/speach.tex`](speach/speach.tex) | Detailed speaker notes/script organized by slide. The directory spelling is retained as it exists in the project. |
| [`speach/speach.pdf`](speach/speach.pdf) | Compiled speaker script. |
| `imagenes/logo1.png`, `imagenes/logo2.png` | Local image assets available to the project. |
| [`requirements.txt`](requirements.txt) | Python dependencies listed for related federated-learning work: Flower, PyTorch, torchvision, NumPy, and Matplotlib. It does not install RabbitMQ or LaTeX. |
| `*.aux`, `*.log`, `*.nav`, `*.toc`, `*.fls`, and similar files | LaTeX build byproducts. They are regenerated during compilation and are not the editable document sources. |

The main architecture figure in `proposal.tex` is drawn using TikZ, so it is not a separate image file.

## Compile the LaTeX documents

Run commands from this folder so local paths such as `Definitions/mdpi` resolve. You need MiKTeX or TeX Live with the MDPI template dependencies, Beamer, TikZ/PGFPlots, and `listings`.

### Proposal

```powershell
cd C:\Users\User\Desktop\8vo\Sistemas-Distribuidos\Proyect-Machine-Distributed\proporsal
pdflatex -interaction=nonstopmode -halt-on-error proposal.tex
pdflatex -interaction=nonstopmode -halt-on-error proposal.tex
```

The second pass resolves citations, labels, and page references. The MDPI class is supplied locally in `Definitions/`.

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

The Python packages can be installed with:

```powershell
python -m pip install -r requirements.txt
```

This installs Python libraries only. It does not install/start a RabbitMQ broker, create the distributed application, or compile LaTeX documents.

## Terminology and interpretation notes

- **Federated learning:** participants keep training data locally and exchange model updates for collaborative training.
- **Broker/middleware:** RabbitMQ routes and buffers messages; it does not train or aggregate the model by itself.
- **Coordinator:** application component that sends round instructions, validates responses, applies the aggregation rule, and publishes model versions.
- **Client/worker:** farm-side process that receives a version, trains locally, and reports an update.
- **Non-IID:** clients' data distributions differ from one another.
- **Client drift:** local optimization moves client models in different directions because their data differs.
- **Quorum:** configured minimum set/count of worker responses accepted for a round; not synonymous with consensus.
- **Preliminary prototype result:** protocol-level result using synthetic updates; not a full PlantVillage CNN performance result.
- **Planned deliverable:** a target in the presentation/work plan; do not call it implemented until code and evidence support that status.

### Consistency notes for the slide source

The README uses RabbitMQ/AMQP for the coordinator-worker message paths, matching the proposal's architecture. The current slide deck also uses “gRPC”/“RPC” wording in a few places; if the implementation uses RabbitMQ only, those terms should be changed to RabbitMQ/AMQP messaging to avoid suggesting that a second transport is deployed. Also, a quorum threshold alone does not prevent split brain or create majority consensus; describe it as the coordinator's application-level participation rule unless a separate consensus/fencing mechanism is implemented.

---

**Project guide:** Use the `.tex` sources for edits and keep the matching PDFs current. For claims about implementation status or measured results, consult the latest code, test output, and experiment artifacts.
