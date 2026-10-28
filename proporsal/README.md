# Federated Crop Disease Detection
## Project guide and presentation notes

**Project title:** *Evaluating FedAvg and FedProx for Federated Crop Disease Detection under Data Heterogeneity*  
**Author:** Dario Pomasqui  
**Institution:** Yachay Tech University  
**Course:** Distributed Systems

I wrote this README as a companion to [`presentacion.tex`](presentacion.tex). I follow the same story as my slides: why farms need a distributed solution, how I model the farm nodes and their communication, what FedAvg and FedProx do, and how I plan to evaluate them. I write formulas as plain text/code so they stay readable on GitHub and other Markdown viewers.

> **Current scope:** I am writing a research proposal, not reporting a completed federated-learning study. The only experiments I have run so far are the two activities documented in [`../Workshop6/`](../Workshop6/). They validate RabbitMQ examples and a coordinator/worker protocol with synthetic scalar updates. I have not trained a CNN, processed PlantVillage, or measured classification accuracy/F1.

## Contents

- [The story in one minute](#the-story-in-one-minute)
- [What the final-project instructions ask for](#what-the-final-project-instructions-ask-for)
- [Presentation walkthrough](#presentation-walkthrough)
- [How the distributed design works](#how-the-distributed-design-works)
- [The math without rendering problems](#the-math-without-rendering-problems)
- [Experiments and what they test](#experiments-and-what-they-test)
- [Files in this folder](#files-in-this-folder)
- [Compile the LaTeX documents](#compile-the-latex-documents)
- [Terminology and interpretation notes](#terminology-and-interpretation-notes)

## The story in one minute

I chose this problem because different farms see different crop diseases and use different cameras and growing conditions. Their image collections are therefore not identically distributed. Uploading every photograph to one central repository would also mean giving up local control of sensitive data and transferring large amounts of data over the network.

I use federated learning so each farm can train locally and send model updates to a coordinator. I compare two ways to combine those updates: **FedAvg**, which averages client models according to each client's sample count, and **FedProx**, which adds a penalty to local training to limit how far a client moves from the current global model. **RabbitMQ** carries coordinator/worker messages; I use it as communication middleware, not as the learning algorithm. I model three farms to study data heterogeneity, message flow, synchronization, and a worker dropout scenario.

## What the final-project instructions ask for

In the course instructions, I am asked to submit the **first version of a research paper**, not just a project description. I need to define an AI research question, justify it with scientific literature, explain a feasible experimental method, and include genuine preliminary evidence. I use the checklist below to connect each requirement to my current materials and to keep track of what I still need to verify.

| Course requirement | How it appears in my current work |
|---|---|
| Define a research problem, its relevance, a research question, objective, and expected contribution. | In `proposal.tex`, I explain crop disease classification across farms, data privacy, and non-IID data. I ask whether FedProx improves on FedAvg and state my objectives and expected contributions. |
| Make the topic an AI research project and connect it to Distributed Systems. | I propose federated crop-image classification with a CNN. I connect it to distributed systems through coordinator/worker processes, RabbitMQ messaging, round synchronization, and client dropout. |
| Choose an application or an AI-method contribution and state the novelty. | I propose evaluating the established FedProx method against FedAvg for crop disease data. My proposed contribution is the controlled study of agricultural data heterogeneity and distributed behavior, not a new optimizer. |
| Review scientific literature and identify prior methods, findings, limitations, and a baseline. | In Related Work, I discuss federated optimization, PlantVillage, non-IID data, and smart agriculture. I include a comparison table and scientific references. |
| Describe a complete and reproducible methodology. | In Materials and Methods, I propose PlantVillage, three simulated clients, IID/non-IID partitions, CNN training, FedAvg/FedProx, RabbitMQ, dropout scenarios, and diagnostic/system metrics. These are the planned experiments, not all completed runs. |
| Include a student-designed system diagram. | I include a TikZ architecture draft showing the dataset, farm workers, RabbitMQ, coordinator, evaluation, and edge support. My course instructions prohibit AI-generated diagrams, so the version I submit must be designed or redrawn by me and every component must be explainable. |
| Identify a benchmark and justify the metrics. | I propose FedAvg as the baseline and FedProx as the method under study. I plan to report accuracy, macro-F1, per-class/minority recall, inter-round stability, communication volume, latency, and dropout behavior. |
| Include genuine preliminary experiments and interpret a result. | My only experimental evidence so far comes from Workshop 6. It verifies RabbitMQ queue/fanout behavior, C/Python clients, and synthetic FedAvg aggregation with complete and partial quorum. It does not include an AI model, PlantVillage processing, or classification metrics. |
| Provide a reproducible GitHub repository. | I list Python dependencies in `requirements.txt` and link to [`github.com/darioXxx32/IA`](https://github.com/darioXxx32/IA). Workshop 6 source, instructions, outputs, tests, and screenshots are in [`../Workshop6/`](../Workshop6/). |
| Use MDPI format and the required research-paper sections. | I formatted `proposal.tex` with the local MDPI class in `Definitions/`. It contains the title, abstract, keywords, Introduction, Related Work, Materials and Methods, Preliminary Results, Discussion/Expected Research Direction, and References. |
| Submit the proposal and repository link. Slides are not required. | I include the proposal and repository URL. I also prepared slides and a speaker script as optional supporting material. |

### What my preliminary experiments do and do not show

The Workshop 6 tests are genuine executions of my message-middleware and coordinator/worker code, and they support the feasibility of that distributed part. The Activity 2 updates are deliberately synthetic scalar values; they test routing, acknowledgments, weighted aggregation, and quorum handling. They are not trained model weights. I have not yet run the AI part of the proposed experiment: I have not downloaded or processed PlantVillage, trained a CNN, compared FedAvg with FedProx on images, or calculated accuracy, F1, or class recall. I therefore present those as research plans and do not claim AI classification results.

### Experiments I have completed in Workshop 6

| Activity and test | What I ran | Result supported by the saved evidence |
|---|---|---|
| Activity 1: Python queue | Published `Hello Middleware!` to the durable `hello` queue and received/acknowledged it with a Python consumer. | PASS. The saved test output records delivery and acknowledgment. |
| Activity 1: Python fanout | Published one test message to two independently bound subscriber queues. | PASS. Both queues received the same message. |
| Activity 1: C client | Built the C producer and consumer in an Ubuntu Docker build image with `librabbitmq-dev`; tested delivery through the RabbitMQ broker. | PASS. The C consumer received `Hello from C!`; the C build and output are recorded in the activity evidence. |
| Activity 1: Python checks | Compiled the four supplied Python examples and checked Pika connectivity to the local AMQP port. | PASS. Syntax checks and broker connection passed. |
| Activity 2: complete round | Ran three local farm processes with sample counts 10, 20, and 30 and synthetic scalar updates 1, 2, and 4. | PASS. The coordinator received 3/3 updates and wrote global weight `2.8333333333333335` to `result.json`. |
| Activity 2: Farm C dropout | Ran Farms A and B while leaving Farm C offline; configured quorum 2 and a 3-second collection timeout. | PASS. The coordinator received 2/3 updates and wrote global weight `1.6666666666666667` with status `partial_quorum` to `result-dropout.json`. The saved broker screenshot shows Farm C's queued command. |
| Activity 2: unit tests | Tested the sample-weighted average, rejected mismatched update dimensions, and rejected non-positive sample counts. | PASS. All 3 tests passed. |

I did not measure model accuracy or runtime in these experiments. The `3-second` value above is the timeout configured for the dropout demo, not a measured latency result. The complete-round and dropout JSON files record participants, sample counts, quorum, status, and aggregate weights; they do not record elapsed time.

The full instructions, code, logs, screenshots, and Workshop 6 report are in [`../Workshop6/`](../Workshop6/): [Activity 1 report and evidence](../Workshop6/solution1/resolucion-actividad1/), [Activity 2 source and results](../Workshop6/solution2/), and [combined Workshop 6 PDF report](../Workshop6/solution2/reporte-workshop6.pdf).

For quick review, I link the saved evidence directly: [Activity 1 test summary](../Workshop6/solution1/resolucion-actividad1/evidencias/test-results.txt), [Activity 1 queue screenshot](../Workshop6/solution1/resolucion-actividad1/evidencias/rabbitmq-cola-hello.png), [Activity 1 fanout/exchange screenshot](../Workshop6/solution1/resolucion-actividad1/evidencias/rabbitmq-exchange-logs.png), [Activity 2 complete-round log](../Workshop6/solution2/evidencias/three-farms-run.txt), [Activity 2 partial-quorum log](../Workshop6/solution2/evidencias/partial-quorum-run.txt), [Activity 2 unit-test output](../Workshop6/solution2/evidencias/unit-tests.txt), and [Farm C queued-command screenshot](../Workshop6/solution2/evidencias/rabbitmq-queues-dropout.png).

I ran Activity 1 with Python 3.13.14, Pika 1.4.4, RabbitMQ Management image 3.13.7, Docker Desktop 29.2.1, and GCC 13.2.0. I built the C example in Ubuntu 24.04 with `librabbitmq-dev` 0.11.0. Activity 2 uses the Pika-based Python prototype and the same local RabbitMQ broker. The captured test summaries and terminal outputs are in the Workshop 6 evidence folders linked above.

To rerun the tests, I start RabbitMQ first and then follow the commands in the Workshop 6 READMEs. From the repository root, the core Activity 2 commands are:

```powershell
docker start workshop6-rabbitmq
python -m pip install -r Workshop6/solution2/requirements.txt
python Workshop6/solution2/test_protocol.py
python Workshop6/solution2/run_demo.py
python Workshop6/solution2/run_demo.py --dropout farm-c
```

For Activity 1, I use [`Workshop6/solution1/README.md`](../Workshop6/solution1/README.md) and its PowerShell test script. The C build needs Docker Desktop because I install `librabbitmq-dev` inside the Ubuntu build container rather than relying on a native Windows package. If I have not created the broker container yet, I use the `docker run` command in that README; otherwise I start the existing container with `docker start workshop6-rabbitmq`.

## Presentation walkthrough

Here I follow the narrative of `presentacion.tex` and explain each idea in my own words.

### 1. Title and project scope

I ask whether FedProx can improve crop disease classification when independent farm nodes have different local data. I combine a distributed coordinator/worker design with federated optimization. I simulate the agricultural network; my proposal does not claim to model a deployment across real farms.

### 2. Why agriculture needs collaboration

I focus on crop disease recognition because a model can benefit from varied leaf images, while each producer owns a different subset of those images. Sending every photograph to one central service can raise privacy, commercial confidentiality, storage, and rural connectivity concerns. With federated learning, I aim to share model improvements while keeping raw images at each participant.

### 3. Non-IID data and client drift

I use “non-IID” to mean that my clients do not have matching data distributions. For example, I can assign more rust and blight to one simulated farm, more bacterial spots or mildew to another, and more viral or healthy leaves to a third. I also consider variation in lighting, backgrounds, and camera sensors.

Because each worker trains on its own data, its model can move toward patterns common at that farm. Those local directions may disagree with my global objective. I call this divergence **client drift**. It can make simple averaging unstable and hurt classes that are rare on some clients. I test this possibility without assuming that one optimizer must always win.

### 4. Research question and hypotheses

My central question is whether FedProx improves diagnostic performance, stability across rounds, and generalization across clients compared with FedAvg when farm data is non-IID.

I state four hypotheses in my proposal:

1. Under IID data, FedAvg and FedProx may perform similarly; under stronger skew, FedProx may better preserve macro-F1 and minority-class recall.
2. FedProx's proximal penalty may reduce round-to-round performance oscillations.
3. A middle-range value of `mu` may balance client stability against overly restricted local training.
4. Under a client dropout scenario, FedProx may retain more stable model updates.

I treat these as hypotheses to evaluate, not results guaranteed by my design.

### 5–6. Distributed coordination and round latency

I use one logical coordinator and several workers. In each round, the coordinator sends the current model, clients train, clients return updates, and the coordinator aggregates accepted responses. I model each round as a barrier: it cannot complete until the required responses arrive or my timeout/quorum rule lets it proceed.

I explain the latency model in the slides this way:

```text
round_time = slowest_client(downlink_time + local_compute_time + uplink_time)
             + aggregation_time
```

I call the slowest participating client a **straggler**; it can dominate the round time. More local computation or slower links can reduce my overall throughput. I also plan to track the size of serialized model updates because I expect sending parameters to require less bandwidth than sending all original images. I will only claim a percentage reduction if I calculate it from the model size and image volume in my actual experiment.

### 7. What each farm node contains

I model each farm as an autonomous node with private storage, its own compute, and a local model copy. My nodes do not share memory or a filesystem; they exchange messages through the broker.

In my presentation, I summarize node `k` with this state tuple:

```text
sigma_k = (w_k, D_k, n_k, t_k)
```

- `w_k`: current local model parameters.
- `D_k`: the farm's private dataset, or that farm's assigned benchmark partition in the simulation.
- `n_k`: the number of training examples represented by the client's update.
- `t_k`: the local federated round/model version known to that worker.

I use this as mathematical notation for local state. My program does not have to store these fields in one literal tuple. I keep the dataset at the client; I do not include it in an update message.

### 8. Worker lifecycle and dropout handling

I describe a worker's lifecycle with these states:

```text
IDLE -> SYNCHRONIZING -> TRAINING -> REPORTING
  \                                      /
   +------------ PARTITIONED ------------+
```

- **IDLE:** I have the worker wait for a training instruction.
- **SYNCHRONIZING:** I have it install the global model version for the new round.
- **TRAINING:** I have it perform local epochs on private data.
- **REPORTING:** I have it return the model update and sample count.
- **PARTITIONED:** I treat the worker as unreachable until timeout; the coordinator decides whether my current round can continue with the available clients.

When a disconnected worker returns, I plan to synchronize it with a later global model version. I call this **state catch-up** in the presentation. My client application must consume and install that version; a durable queue alone does not recover the model.

### 9. Architecture and message flow

In my architecture, three farm workers communicate through a RabbitMQ broker with a coordinator. I also include evaluation and a proposed edge-support component:

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

I use `FitIns` for a downlink instruction (round information and global weights) and `FitRes` for an uplink response (updated weights, sample count, and metrics). RabbitMQ routes my messages between workers and coordinator. I keep raw images in each worker's local data partition.

### 10. Data partitions and the farmer support tool

I plan four data regimes to vary the degree of heterogeneity:

- **IID:** clients have approximately balanced class distributions.
- **Low non-IID:** a Dirichlet partition with `alpha = 1.0` creates mild variation.
- **Medium non-IID:** `alpha = 0.5` creates more concentrated class distributions.
- **High non-IID/disjoint:** each farm receives a dominant disease cluster and fewer examples from the others.

The partition seed, partition method, and resulting class counts are not available yet because I have not implemented or run the image-partitioning experiment. I will record them when I run that experiment. My proposed edge tool would run an exported model on a leaf image and return a disease prediction with a confidence score. I mention calibration (for example, temperature scaling and expected calibration error) because a high softmax score is not automatically a reliable probability. I treat agronomic treatment advice as a future product feature, not as a validated recommendation.

### 11. Six experimental tracks

I organize my evaluation into six tracks:

1. Compare FedAvg and FedProx on global performance and convergence.
2. Measure the effect of increasingly non-IID partitions.
3. Sweep the FedProx penalty `mu` across `0.001`, `0.01`, `0.1`, and `1.0`.
4. Disconnect a worker during training and assess the round protocol.
5. Measure serialized communication size and round/barrier latency.
6. Measure per-client performance and recall for minority disease classes.

I define a stability metric as the sample standard deviation of the round-to-round accuracy changes:

```text
S_delta_acc = standard_deviation(delta_acc_2, ..., delta_acc_R)
```

When I obtain a lower value, it means the measured accuracy changes vary less across rounds. That value alone does not prove better final accuracy or convergence.

### 12. Preliminary RabbitMQ prototype tests

For Activity 2, I ran the Python coordinator and farm clients from Workshop 6 with synthetic scalar updates. This test checks the message protocol and FedAvg arithmetic; it does not train or evaluate a crop-disease model.

| Scenario | Responding clients | Samples | Aggregate recorded in JSON | Protocol observation |
|---|---:|---:|---:|---|
| Complete round | 3 of 3 | 60 | 2.8333333333333335 | All three results were accepted and the round status was `quorum_complete`. |
| Farm C offline | 2 of 3 | 30 | 1.6666666666666667 | The configured quorum was 2; the round status was `partial_quorum`, and Farm C's durable command remained queued. |

For the complete round, I used sample counts 10, 20, and 30 with toy scalar updates 1, 2, and 4:

```text
(10 * 1 + 20 * 2 + 30 * 4) / (10 + 20 + 30)
= 170 / 60
= 2.8333
```

With Farm C offline, the coordinator used only A and B:

```text
(10 * 1 + 20 * 2) / (10 + 20)
= 50 / 30
= 1.6667
```

These values verify the expected sample-weighted arithmetic for the supplied synthetic inputs. They are not CNN accuracy results and do not show how FedAvg/FedProx perform on PlantVillage. The dropout demo uses a configured 3-second timeout, but I did not save a measured runtime or latency value, so I do not report one here.

### 13. Distributed systems concepts

In my design, I use message passing, round identifiers, timeouts, duplicate suppression, and weighted aggregation. I describe the causal order of messages as:

```text
broadcast instruction -> local training -> upload result -> aggregation
```

I use round and client identifiers so the coordinator can reject duplicate results. While it is healthy, my single logical writer assigns global model versions so workers do not independently commit separate versions. My proposal does not replicate the coordinator or implement coordinator failover.

I use CAP terminology in my slides to discuss availability and network partitions. I intend this as a design discussion, not a formal CAP proof: my coordinator/barrier still controls whether a global round can advance, and local training while disconnected is not the same as committing a globally consistent model.

### 14. Software deliverables and edge deployment

I separate my proposed software pipeline into:

- federated training simulation (Python, PyTorch, Flower/RabbitMQ components as implemented),
- dataset partitioning and evaluation,
- model export (the slides mention ONNX or TorchScript), and
- a lightweight C++ edge inference runtime.

I list the C++ runtime and sub-50-ms inference figure as planned targets, not results demonstrated by my current proposal PDF. I will only claim them as completed after I implement and measure them on a specified device.

### 15–16. Schedule, reproducibility, and final report

I lay out six proposed phases, from the message-middleware prototype through CNN training, benchmark tracks, edge export, and final analysis. The experimental evidence currently available in this repository is only from Workshop 6. I have not run the PlantVillage partitioning or CNN/FedAvg/FedProx experiments described in the later phases, so I treat those as planned work rather than completed results.

For repeatable experiments, I plan to record the source revision, dataset and partition configuration, random seed, client count, algorithm and hyperparameters, broker settings, timeout/quorum, test command, and generated results. The Workshop 6 records cover the middleware tests and synthetic-update demonstration; they do not contain the dataset or CNN settings because that experiment has not been run. In the final report, I will distinguish protocol verification from model-performance evaluation and include plots/tables generated from the corresponding result files.

### 17. Conclusion

I expect to contribute a controlled study connecting federated optimization with distributed-system behavior in a crop-disease setting. I am not only asking which algorithm gets the highest score; I want to understand how data skew, local optimization, message timing, and worker availability affect the quality and stability of the shared model.

## How the distributed design works

### Middleware: RabbitMQ

I use RabbitMQ as a message broker implementing AMQP. RabbitMQ is a service (which I can run in a container); it is not a Python library or the federated learning algorithm. My Python workers need a client library to connect to it. My current [`requirements.txt`](requirements.txt) lists `flwr`, `torch`, `torchvision`, `numpy`, and `matplotlib`, but it does **not** list `pika` or install/start a RabbitMQ server.

I use two logical message paths in the proposal:

| Direction | Message | Purpose |
|---|---|---|
| Coordinator to workers | `FitIns` | Round/version and global model parameters for local training. |
| Workers to coordinator | `FitRes` | Updated parameters, sample count, round identifier, and metrics. |

In the proposal, I specify a durable direct route for commands and topic routing for results as the intended architecture. The Workshop 6 prototype verifies RabbitMQ message delivery and acknowledgments in its examples, but it does not implement the full `FitIns`/`FitRes` model-training protocol or verify every production setting such as publisher confirms, retry policy, and recovery after coordinator failure. I therefore treat those details as design requirements for the next implementation stage, not as completed tests.

### Quorum and system boundaries

I use a minimum quorum as an application rule: it tells my coordinator whether enough responses arrived to process a round. A timeout bounds the wait. If a worker is absent and my configured minimum is met, I can re-normalize the sample weights over the responding set.

I do not treat this mechanism as consensus or RabbitMQ as a consensus service. It does not automatically provide majority consensus, replicated coordinator state, split-brain prevention during coordinator failure, or Byzantine fault tolerance. For my dropout experiment, I assume fail-stop workers; I would need separate mechanisms to handle malicious or corrupted updates.

## The math without rendering problems

I write the expressions below as plain text rather than LaTeX so a Markdown viewer displays them without exposing TeX commands.

### FedAvg aggregation

```text
w_global_next = sum over participating clients k of:
                (n_k / sum of n_j for participating clients) * w_k_next
```

I weight each client according to its number of local examples. `w_k_next` is the model after client `k` trains for the current round.

### FedProx local objective

```text
local_objective_k(w) = F_k(w) + (mu / 2) * ||w - w_global_current||^2
```

I use `F_k(w)` for the farm's local training loss. `mu` controls the strength of my penalty. It is zero at the round's starting global model and grows as the local model moves farther away.

### Round time

```text
round_time = max over participating clients k of:
             (downlink_k + local_compute_k + uplink_k)
             + aggregation_time
```

I use this model to show the straggler effect: with a full barrier, one slow participant can determine the duration of my round.

### Local-state tuple

```text
sigma_k = (w_k, D_k, n_k, t_k)
```

I use this notation to summarize the local model, local dataset, sample count, and known round/version. It describes node state; it does not have to be one literal Python tuple.

## Experiments proposed for the research study

The following table describes the experiments I propose to run after the Workshop 6 middleware work. These are part of my methodology; they are not results I have already obtained.

| Planned experiment | What I would vary | What I would measure |
|---|---|---|
| FedAvg vs. FedProx | the optimization method | global loss/accuracy and rounds to the stopping condition |
| Data heterogeneity | IID through stronger non-IID partitions | partition recipe, per-client class counts, macro-F1, per-class recall |
| FedProx parameter | `mu` in the planned sweep | performance and inter-round stability for each value |
| Client availability | a worker dropout during a round | quorum outcome, timeout behavior, model version, recovery behavior |
| Communication | serialized update size and message path | payload per round and measured round/barrier time |

I will report the actual configuration and preserve the generated outputs for each run. I will keep protocol tests separate from CNN metrics and avoid generalizing from a single synthetic update test.

## Files in this folder

| Path | Purpose |
|---|---|
| [`proposal.tex`](proposal.tex) | My main research proposal. I use the MDPI class to present the research design, architecture, experiments, preliminary protocol validation, schedule, and bibliography. |
| [`proposal.pdf`](proposal.pdf) | The PDF I generate from `proposal.tex`. I rebuild it after editing the source. |
| [`Definitions/`](Definitions/) | I keep the local MDPI class, bibliography styles, journal metadata, and logos here so the proposal can compile. I keep this directory beside `proposal.tex`. |
| [`presentacion.tex`](presentacion.tex) | My 17-slide Beamer presentation, which I use as the outline for this README. |
| [`presentacion.pdf`](presentacion.pdf) | The PDF I generate from my slide source. |
| [`speach/speach.tex`](speach/speach.tex) | My detailed speaker notes, organized by slide. I keep the existing directory spelling `speach`. |
| [`speach/speach.pdf`](speach/speach.pdf) | The PDF I generate from my speaker script. |
| `imagenes/logo1.png`, `imagenes/logo2.png` | Local image files that I keep available for the project documents. |
| [`requirements.txt`](requirements.txt) | I list the Python dependencies for my related federated-learning work here: Flower, PyTorch, torchvision, NumPy, and Matplotlib. I do not install RabbitMQ or LaTeX with this file. |
| `*.aux`, `*.log`, `*.nav`, `*.toc`, `*.fls`, and similar files | LaTeX build files that I let the compiler regenerate; I edit the `.tex` sources instead. |

I define the main architecture figure directly in `proposal.tex` using TikZ, so I do not need a separate diagram image file.

## Compile the LaTeX documents

I run the commands from this folder so local paths such as `Definitions/mdpi` resolve. I need MiKTeX or TeX Live with the MDPI template dependencies, Beamer, TikZ/PGFPlots, and `listings` installed.

### Proposal

```powershell
cd C:\Users\User\Desktop\8vo\Sistemas-Distribuidos\Proyect-Machine-Distributed\proporsal
pdflatex -interaction=nonstopmode -halt-on-error proposal.tex
pdflatex -interaction=nonstopmode -halt-on-error proposal.tex
```

I run the second pass to resolve citations, labels, and page references. I keep the MDPI class locally in `Definitions/`.

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

I install the Python packages with:

```powershell
python -m pip install -r requirements.txt
```

When I run this command, I install Python libraries only. It does not install/start my RabbitMQ broker, create the distributed application, or compile LaTeX documents.

## Terminology and interpretation notes

- **Federated learning:** I keep training data on each participant and exchange model updates to train a shared model.
- **Broker/middleware:** I use RabbitMQ to route and buffer messages; it does not train or aggregate my model by itself.
- **Coordinator:** my application component sends round instructions, validates responses, applies the aggregation rule, and publishes model versions.
- **Client/worker:** my farm-side process receives a version, trains locally, and reports an update.
- **Non-IID:** I use this term when clients' data distributions differ from one another.
- **Client drift:** I use this term for local optimization moving client models in different directions because their data differs.
- **Quorum:** I set a minimum number of worker responses to accept for a round; I do not use quorum as a synonym for consensus.
- **Preliminary prototype result:** I use this label for my protocol-level test with synthetic updates; it is not a full PlantVillage CNN performance result.
- **Planned deliverable:** I use this label for a target in my work plan; I will call it implemented only when I have code and evidence to support that status.

### What I have and have not verified

I tested RabbitMQ message delivery and a small coordinator/worker aggregation flow in Workshop 6. That prototype uses RabbitMQ/AMQP and synthetic scalar values. It does not establish that the proposed full federated-learning architecture has been deployed, nor does it provide replicated coordinator state, failover fencing, majority consensus, or split-brain protection. My configured quorum is only an application-level rule for deciding whether enough worker responses have arrived. I keep these system guarantees separate from the middleware behavior demonstrated by the current tests.

---

**How I maintain this folder:** I edit the `.tex` sources and regenerate the matching PDFs. When I make claims about implementation status or measured results, I check them against my latest code, test output, and experiment artifacts.
