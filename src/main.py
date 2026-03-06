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
        'delivery_ratio': delivery_ratio,
        'generated_events': metrics["generated_events"],
        'received_by_ch': metrics["received_by_ch"],
        'received_by_bs': metrics["received_by_bs"]
    }

def display_results(results):
    for res in results:
        print(f"\n--- {res['name']} ---")
        print(f"Events generated: mean={res['generated_events']['mean']:.1f}, min={res['generated_events']['min']}, max={res['generated_events']['max']}")
        print(f"Events received by CH: mean={res['received_by_ch']['mean']:.1f}, min={res['received_by_ch']['min']}, max={res['received_by_ch']['max']}")
        print(f"Events received by BS: mean={res['received_by_bs']['mean']:.1f}, min={res['received_by_bs']['min']}, max={res['received_by_bs']['max']}")
        print(f"Delivery ratio: mean={res['delivery_ratio']['mean']:.4f}, min={res['delivery_ratio']['min']:.4f}, max={res['delivery_ratio']['max']:.4f}")
        if res['fnd']['mean'] is not None:
            print(f"FND: mean={res['fnd']['mean']:.2f}, min={res['fnd']['min']:.2f}, max={res['fnd']['max']:.2f}")
        else:
            print("FND: not reached")
        if res['hnd']['mean'] is not None:
            print(f"HND: mean={res['hnd']['mean']:.2f}, min={res['hnd']['min']:.2f}, max={res['hnd']['max']:.2f}")
        else:
            print("HND: not reached")
        if res['lnd']['mean'] is not None:
            print(f"LND: mean={res['lnd']['mean']:.2f}, min={res['lnd']['min']:.2f}, max={res['lnd']['max']:.2f}")
        else:
            print("LND: not reached")

    # Plots using means
    if len(results) > 0:
        plt.figure()
        for res in results:
            plt.plot(res['metrics']["time"]["mean"], res['metrics']["delivery_ratio"]["mean"], label=res['name'])
        plt.xlabel("Time")
        plt.ylabel("Delivery Ratio")
        plt.title("Delivery Ratio Comparison (Mean)")
        plt.ylim(0, 1)
        plt.grid(True)
        plt.legend()

        plt.figure()
        for res in results:
            plt.plot(res['metrics']["time"]["mean"], res['metrics']["alive_nodes"]["mean"], label=res['name'])
        plt.xlabel("Time")
        plt.ylabel("Number of Alive Nodes")
        plt.title("Alive Nodes Over Time (Mean)")
        plt.grid(True)
        plt.legend()

        total_nodes = results[0]['nb_nodes']
        plt.figure()
        for res in results:
            dead = [total_nodes - a for a in res['metrics']["alive_nodes"]["mean"]]
            plt.plot(res['metrics']["time"]["mean"], dead, label=res['name'])
        plt.xlabel("Time")
        plt.ylabel("Number of Dead Nodes")
        plt.title("Dead Nodes Over Time (Mean)")
        plt.grid(True)
        plt.legend()

        plt.figure()
        for res in results:
            plt.plot(res['metrics']["time"]["mean"], res['metrics']["received_by_bs_ts"]["mean"], label=res['name'])
        plt.xlabel("Time")
        plt.ylabel("Cumulative Data Received at BS")
        plt.title("Cumulative Data Delivered to BS (Mean)")
        plt.grid(True)
        plt.legend()

        plt.figure()
        for res in results:
            plt.plot(res['metrics']["time"]["mean"], res['metrics']["energy_total"]["mean"], label=res['name'])
        plt.xlabel("Time")
        plt.ylabel("Total Energy (J)")
        plt.title("Total Network Energy vs Time (Mean)")
        plt.grid(True)
        plt.legend()

        
        plt.show()

def aggregate_results(results_list):
    if not results_list:
        return None
    
    # Assume all have same nb_nodes
    nb_nodes = results_list[0]['nb_nodes']
    
    # Aggregate scalars
    delivery_ratios = [r['delivery_ratio'] for r in results_list]
    generated_events = [r['generated_events'] for r in results_list]
    received_by_ch = [r['received_by_ch'] for r in results_list]
    received_by_bs = [r['received_by_bs'] for r in results_list]
    fnds = [r['fnd'] for r in results_list if r['fnd'] is not None]
    hnds = [r['hnd'] for r in results_list if r['hnd'] is not None]
    lnds = [r['lnd'] for r in results_list if r['lnd'] is not None]
    
    aggregated = {
        'name': results_list[0]['name'],
        'nb_nodes': nb_nodes,
        'delivery_ratio': {
            'mean': sum(delivery_ratios) / len(delivery_ratios),
            'min': min(delivery_ratios),
            'max': max(delivery_ratios)
        },
        'generated_events': {
            'mean': sum(generated_events) / len(generated_events),
            'min': min(generated_events),
            'max': max(generated_events)
        },
        'received_by_ch': {
            'mean': sum(received_by_ch) / len(received_by_ch),
            'min': min(received_by_ch),
            'max': max(received_by_ch)
        },
        'received_by_bs': {
            'mean': sum(received_by_bs) / len(received_by_bs),
            'min': min(received_by_bs),
            'max': max(received_by_bs)
        },
        'fnd': {
            'mean': sum(fnds) / len(fnds) if fnds else None,
            'min': min(fnds) if fnds else None,
            'max': max(fnds) if fnds else None
        },
        'hnd': {
            'mean': sum(hnds) / len(hnds) if hnds else None,
            'min': min(hnds) if hnds else None,
            'max': max(hnds) if hnds else None
        },
        'lnd': {
            'mean': sum(lnds) / len(lnds) if lnds else None,
            'min': min(lnds) if lnds else None,
            'max': max(lnds) if lnds else None
        }
    }
    
    # Aggregate lists: find min length, average point-wise
    min_len = min(len(r['metrics']['time']) for r in results_list)
    aggregated['metrics'] = {}
    list_keys = ['time', 'alive_nodes', 'delivery_ratio', 'received_by_bs_ts', 'energy_total']
    for key in list_keys:
        values = [r['metrics'][key][:min_len] for r in results_list]
        aggregated['metrics'][key] = {
            'mean': [sum(v[i] for v in values) / len(values) for i in range(min_len)],
            'min': [min(v[i] for v in values) for i in range(min_len)],
            'max': [max(v[i] for v in values) for i in range(min_len)]
        }
    
    return aggregated

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run WSN simulations")
    parser.add_argument('-s', '--simulations', nargs='+', choices=['L', 'H', 'D'], required=True,
                        help="Simulations to run: L for LEACH, H for HEED, D for DEECRP")
    parser.add_argument('-n', '--runs', type=int, default=1,
                        help="Number of runs per simulation (default: 1)")
    args = parser.parse_args()

    sensor_classes = {
        'L': (LeachSensors, generate_random, 'LEACH'),
        'H': (HeedSensors, generate_random, 'HEED'),
        'D': (DeecrpSensors, generate_grid, 'DEECRP')
    }

    results = []
    for sim in args.simulations:
        SensorClass, generator, name = sensor_classes[sim]
        sim_results = []
        for run in range(args.runs):
            result = run_and_analyze(SensorClass, generator, name, seed=42 + run)  # Different seed per run
            sim_results.append(result)
        aggregated = aggregate_results(sim_results)
        results.append(aggregated)

    display_results(results)


