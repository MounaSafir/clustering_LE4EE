import simpy
import random
import os
import matplotlib.pyplot as plt
import numpy as np

from simu.environment import Environment
from simu.config import Config
from simu.generate_sensors import generate_random, generate_grid

from simu.leach.leach_sensor import LeachSensors
from simu.heed.heed_sensor import HeedSensors
from simu.deecrp.deecrp_sensor import DeecrpSensors



N_RUNS = 20                 # Number of independent simulations
BASE_SEED = 42              # Base seed for reproducibility
FIG_DIR = "figures"         # Output directory for plots

os.makedirs(FIG_DIR, exist_ok=True)




def run_simulation(SensorClass, generator, seed):
    random.seed(seed)

    simpy_env = simpy.Environment()
    config = Config(lambda id, config: generator(id, config, SensorClass))
    env = Environment(config)

    simpy_env.process(env.main(simpy_env))
    simpy_env.run()

    return env


def run_multiple(SensorClass, generator):
    all_metrics = []

    for i in range(N_RUNS):
        env = run_simulation(
            SensorClass,
            generator,
            seed=BASE_SEED + i
        )
        all_metrics.append(env.metric.data)

    # Return metrics and one reference environment
    return all_metrics, env




def DeecrpNoRouting(position, id, config):
    return DeecrpSensors(position, id, config, use_routing=False)


def DeecrpWithRouting(position, id, config):
    return DeecrpSensors(position, id, config, use_routing=True)




def mean_time_series(all_metrics, key):
    min_len = min(len(m[key]) for m in all_metrics)

    return [
        sum(m[key][t] for m in all_metrics) / len(all_metrics)
        for t in range(min_len)
    ]


def final_delivery_ratio(all_metrics):
    ratios = []

    for m in all_metrics:
        generated = m["generated_events"]
        received  = m["received_by_bs"]
        ratios.append(received / generated if generated > 0 else 0)

    return np.mean(ratios)


def compute_lifetime(metrics, nb_nodes):
    fnd = hnd = lnd = None

    for t, alive in zip(metrics["time"], metrics["alive_nodes"]):
        if fnd is None and alive < nb_nodes:
            fnd = t
        if hnd is None and alive <= nb_nodes / 2:
            hnd = t
        if lnd is None and alive == 0:
            lnd = t

    return fnd, hnd, lnd


def mean_lifetime(all_metrics, nb_nodes):
    fnd, hnd, lnd = [], [], []

    for m in all_metrics:
        f, h, l = compute_lifetime(m, nb_nodes)
        if f is not None: fnd.append(f)
        if h is not None: hnd.append(h)
        if l is not None: lnd.append(l)

    return np.mean(fnd), np.mean(hnd), np.mean(lnd)




def energy_efficiency_packets_per_joule(mean_energy, mean_packets):
    """
    Energy efficiency metric:
    Number of packets delivered per unit of energy.
    
    Unit: packets / joule
    """
    efficiency = []

    for t in range(len(mean_packets)):
        if mean_energy[t] > 0:
            efficiency.append(mean_packets[t] / mean_energy[t])
        else:
            efficiency.append(0)

    return efficiency


def packets_per_alive_node(mean_packets, mean_alive):
    """
    Network productivity metric:
    Number of packets delivered per alive node.
    """
    ratio = []

    for t in range(min(len(mean_packets), len(mean_alive))):
        if mean_alive[t] > 0:
            ratio.append(mean_packets[t] / mean_alive[t])
        else:
            ratio.append(0)

    return ratio



def save_plot(x, curves, labels, title, ylabel, filename):
    plt.figure()
    for y, lbl in zip(curves, labels):
        plt.plot(x[:len(y)], y, linewidth=2, label=lbl)

    plt.xlabel("Time")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/{filename}", dpi=300)
    plt.close()


metrics_leach, env_ref = run_multiple(LeachSensors, generate_random)
metrics_heed, _       = run_multiple(HeedSensors, generate_random)
metrics_nr, _         = run_multiple(DeecrpNoRouting, generate_grid)
metrics_rt, _         = run_multiple(DeecrpWithRouting, generate_grid)

nb_nodes = len(env_ref.sensors)
time = metrics_leach[0]["time"]




mean_alive = {
    "LEACH":     mean_time_series(metrics_leach, "alive_nodes"),
    "HEED":      mean_time_series(metrics_heed, "alive_nodes"),
    "DEECRP_nr": mean_time_series(metrics_nr, "alive_nodes"),
    "DEECRP_rt": mean_time_series(metrics_rt, "alive_nodes"),
}

mean_packets = {
    "LEACH":     mean_time_series(metrics_leach, "received_by_bs_ts"),
    "HEED":      mean_time_series(metrics_heed, "received_by_bs_ts"),
    "DEECRP_nr": mean_time_series(metrics_nr, "received_by_bs_ts"),
    "DEECRP_rt": mean_time_series(metrics_rt, "received_by_bs_ts"),
}

mean_energy = {
    "LEACH":     mean_time_series(metrics_leach, "energy_total"),
    "HEED":      mean_time_series(metrics_heed, "energy_total"),
    "DEECRP_nr": mean_time_series(metrics_nr, "energy_total"),
    "DEECRP_rt": mean_time_series(metrics_rt, "energy_total"),
}




print("\n===== FINAL RESULTS (AVERAGED OVER RUNS) =====")

for name, metrics in [
    ("LEACH", metrics_leach),
    ("HEED", metrics_heed),
    ("DEECRP_nr", metrics_nr),
    ("DEECRP_rt", metrics_rt),
]:
    dr = final_delivery_ratio(metrics)
    fnd, hnd, lnd = mean_lifetime(metrics, nb_nodes)

    print(f"\n--- {name} ---")
    print(f"Delivery Ratio     : {dr:.4f}")
    print(f"FND / HND / LND    : {fnd:.1f} / {hnd:.1f} / {lnd:.1f}")




energy_eff = {
    k: energy_efficiency_packets_per_joule(mean_energy[k], mean_packets[k])
    for k in mean_energy
}

packets_alive = {
    k: packets_per_alive_node(mean_packets[k], mean_alive[k])
    for k in mean_alive
}

final_energy_eff = {
    k: mean_packets[k][-1] / mean_energy[k][-1]
    for k in mean_energy
}



save_plot(
    time,
    mean_alive.values(),
    mean_alive.keys(),
    "Alive Nodes Over Time",
    "Alive Nodes",
    "alive_nodes.png"
)

save_plot(
    time,
    mean_packets.values(),
    mean_packets.keys(),
    "Cumulative Packets Received at Base Station",
    "Packets",
    "packets_bs.png"
)

save_plot(
    time,
    mean_energy.values(),
    mean_energy.keys(),
    "Total Network Energy Consumption",
    "Energy (J)",
    "energy_total.png"
)

save_plot(
    time,
    energy_eff.values(),
    energy_eff.keys(),
    "Energy Efficiency Over Time",
    "Packets / Joule",
    "energy_efficiency.png"
)

save_plot(
    time,
    packets_alive.values(),
    packets_alive.keys(),
    "Packets Received per Alive Node",
    "Packets / Alive Node",
    "packets_per_alive_node.png"
)


# ============================================================


plt.figure(figsize=(6, 4))
plt.bar(final_energy_eff.keys(), final_energy_eff.values())
plt.ylabel("Packets / Joule")
plt.title("Final Energy Efficiency Comparison")
plt.grid(axis="y")
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/energy_efficiency_bar.png", dpi=300)
plt.close()

