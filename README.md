# Event-Based Simulation of Clustering Algorithms for WSN

This project implements an **event-based simulation framework** for evaluating classical clustering algorithms used in **Wireless Sensor Networks (WSN)**.

The following algorithms were adapted from their traditional round-based implementations to an **event-driven simulation model**:

* **LEACH** — Low-Energy Adaptive Clustering Hierarchy
* **HEED** — Hybrid Energy-Efficient Distributed Clustering
* **DEECRP** — Distributed Energy-Efficient Clustering Routing Protocol

The goal is to study how these protocols behave in a **fully asynchronous environment**, where actions are triggered by events instead of synchronous rounds.

---

# Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

# Running Simulations

## Run a single simulation

```bash
python main.py
```

This runs **one simulation instance** and displays the results.

---

## Run multiple simulations (average results)

You can run multiple simulations to compute averaged metrics.

```bash
python main_mean.py
```

or using command line options:

```bash
python main.py -s L -n 20
```

Where:

* `-s` selects the clustering algorithm
* `-n` specifies the number of simulations

Available algorithms:

* `L` → LEACH
* `H` → HEED
* `D` → DEECRP (no routing)
* `Dr` → DEECRP (with routing)

Example running all protocols:

```bash
python main.py -s L H D Dr -n 20
```

---

# Saving Results

Add the `--save` option to store the figures and statistics:

```bash
python main.py -s L H D Dr -n 20 --save
```

The results will be saved in the `results/` directory.

---

# Output

The simulator generates:

* network lifetime metrics
* number of alive/dead nodes
* total network energy
* cumulative packets received at the base station
* comparison plots between protocols

Generated figures include:


* alive nodes over time
* dead nodes over time
* packets received by the base station
* total network energy
* energy efficiency comparison
* network lifetime comparison (FND, HND, LND)

---

# Purpose

This simulator was developed to analyze how traditional **round-based clustering protocols** behave when adapted to a **fully asynchronous event-driven system**.

It is mainly intended for **research experiments and protocol comparison**.
