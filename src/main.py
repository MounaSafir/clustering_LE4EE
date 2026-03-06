import simpy
import random
import matplotlib.pyplot as plt
import argparse

from simu.environment import Environment
from simu.config import Config
from simu.generate_sensors import generate_random , generate_grid

from simu.leach.leach_sensor import LeachSensors
from simu.heed.heed_sensor import HeedSensors
from simu.deecrp.deecrp_sensor import DeecrpSensors



def run_simulation(SensorClass, generator, seed=42):
    random.seed(seed)

    simpy_env = simpy.Environment()
    config = Config(lambda id, config: generator(id, config, SensorClass))
    env = Environment(config)

    simpy_env.process(env.main(simpy_env))
    simpy_env.run()

    return env  

def final_delivery_ratio(metrics):
    gen = metrics["generated_events"]
    rec = metrics["received_by_bs"]
    return rec / gen if gen > 0 else 0


def compute_lifetime(metrics, nb_nodes):
    times = metrics["time"]
    alive = metrics["alive_nodes"]

    fnd = None
    hnd = None
    lnd = None

    for t, a in zip(times, alive):
        # First Node Dies
        if fnd is None and a < nb_nodes:
            fnd = t

        # Half Nodes Die
        if hnd is None and a <= nb_nodes / 2:
            hnd = t

        # Last Node Dies
        if lnd is None and a == 0:
            lnd = t

    return fnd, hnd, lnd

def run_and_analyze(SensorClass, generator, name, seed=42):
    env = run_simulation(SensorClass, generator, seed)
    metrics = env.metric.data
    nb_nodes = len(env.sensors)
    fnd, hnd, lnd = compute_lifetime(metrics, nb_nodes)
    delivery_ratio = final_delivery_ratio(metrics)
    return {
        'name': name,
        'metrics': metrics,
        'nb_nodes': nb_nodes,
        'fnd': fnd,
        'hnd': hnd,
        'lnd': lnd,
        'delivery_ratio': delivery_ratio
    }

def display_results(results):
    for res in results:
        print(f"\n--- {res['name']} ---")
        print("Events generated:", res['metrics']["generated_events"])
        print("Events received by CH:", res['metrics']["received_by_ch"])
        print("Events received by BS:", res['metrics']["received_by_bs"])
        print(f"Delivery ratio: {res['delivery_ratio']:.4f}")
        print("FND:", res['fnd'])
        print("HND:", res['hnd'] if res['hnd'] is not None else "not reached")
        print("LND:", res['lnd'] if res['lnd'] is not None else "not reached")

    # Plots
    if len(results) > 0:
        plt.figure()
        for res in results:
            plt.plot(res['metrics']["time"], res['metrics']["delivery_ratio"], label=res['name'])
        plt.xlabel("Time")
        plt.ylabel("Delivery Ratio")
        plt.title("Delivery Ratio Comparison")
        plt.ylim(0, 1)
        plt.grid(True)
        plt.legend()
        plt.show()

        plt.figure()
        for res in results:
            plt.plot(res['metrics']["time"], res['metrics']["alive_nodes"], label=res['name'])
        plt.xlabel("Time")
        plt.ylabel("Number of Alive Nodes")
        plt.title("Alive Nodes Over Time")
        plt.grid(True)
        plt.legend()
        plt.show()

        total_nodes = results[0]['nb_nodes']
        plt.figure()
        for res in results:
            dead = [total_nodes - a for a in res['metrics']["alive_nodes"]]
            plt.plot(res['metrics']["time"], dead, label=res['name'])
        plt.xlabel("Time")
        plt.ylabel("Number of Dead Nodes")
        plt.title("Dead Nodes Over Time")
        plt.grid(True)
        plt.legend()
        plt.show()

        plt.figure()
        for res in results:
            plt.plot(res['metrics']["time"], res['metrics']["received_by_bs_ts"], label=res['name'])
        plt.xlabel("Time")
        plt.ylabel("Cumulative Data Received at BS")
        plt.title("Cumulative Data Delivered to BS")
        plt.grid(True)
        plt.legend()
        plt.show()

        plt.figure()
        for res in results:
            plt.plot(res['metrics']["time"], res['metrics']["energy_total"], label=res['name'])
        plt.xlabel("Time")
        plt.ylabel("Total Energy (J)")
        plt.title("Total Network Energy vs Time")
        plt.grid(True)
        plt.legend()
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run WSN simulations")
    parser.add_argument('-s', '--simulations', nargs='+', choices=['L', 'H', 'D'], required=True,
                        help="Simulations to run: L for LEACH, H for HEED, D for DEECRP")
    args = parser.parse_args()

    sensor_classes = {
        'L': (LeachSensors, generate_random, 'LEACH'),
        'H': (HeedSensors, generate_random, 'HEED'),
        'D': (DeecrpSensors, generate_grid, 'DEECRP')
    }

    results = []
    for sim in args.simulations:
        SensorClass, generator, name = sensor_classes[sim]
        result = run_and_analyze(SensorClass, generator, name)
        results.append(result)

    display_results(results)


