import simpy
import random
import matplotlib.pyplot as plt

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


env_leach = run_simulation(LeachSensors, generate_random, seed=42)
env_heed  = run_simulation(HeedSensors, generate_random, seed=42)
env_deecrp = run_simulation(DeecrpSensors, generate_grid, seed=42)

metrics_leach = env_leach.metric.data
metrics_heed  = env_heed.metric.data
metrics_deecrp = env_deecrp.metric.data

nb_nodes = len(env_leach.sensors)

fnd_l, hnd_l, lnd_l = compute_lifetime(metrics_leach, nb_nodes)
fnd_h, hnd_h, lnd_h = compute_lifetime(metrics_heed,  nb_nodes)
fnd_d, hnd_d, lnd_d = compute_lifetime(metrics_deecrp,  nb_nodes)



print("\n--- LEACH ---")
print("Events generated:", metrics_leach["generated_events"])
print("Events received by CH:", metrics_leach["received_by_ch"])
print("Events received by BS:", metrics_leach["received_by_bs"])
print(f"Delivery ratio: {final_delivery_ratio(metrics_leach):.4f}")
print("FND:", fnd_l)
print("HND:", hnd_l if hnd_l is not None else "not reached")
print("LND:", lnd_l if lnd_l is not None else "not reached")


print("\n--- HEED ---")
print("Events generated:", metrics_heed["generated_events"])
print("Events received by CH:", metrics_heed["received_by_ch"])
print("Events receivedived by BS:", metrics_heed["received_by_bs"])
print(f"Delivery ratio: {final_delivery_ratio(metrics_heed):.4f}")
print("FND:", fnd_h)
print("HND:", hnd_h if hnd_h is not None else "not reached")
print("LND:", lnd_h if lnd_h is not None else "not reached")


print("\n--- DEECRP ---")
print("Events generated:", metrics_deecrp["generated_events"])
print("Events received by CH:", metrics_deecrp["received_by_ch"])
print("Events receivedived by BS:", metrics_deecrp["received_by_bs"])
print(f"Delivery ratio: {final_delivery_ratio(metrics_deecrp):.4f}")
print("FND:", fnd_d)
print("HND:", hnd_d if hnd_d is not None else "not reached")
print("LND:", lnd_d if lnd_d is not None else "not reached")


# plt.figure()
# plt.plot(metrics_leach["time"], metrics_leach["energy_avg"], label="LEACH")
# plt.plot(metrics_heed["time"],  metrics_heed["energy_avg"],  label="HEED")
# plt.plot(metrics_deecrp["time"],  metrics_deecrp["energy_avg"],  label="DEECRP")
# plt.xlabel("Time")
# plt.ylabel("Average Energy")
# plt.title("Average Energy Comparison")
# plt.grid(True)
# plt.legend()
# plt.show()


plt.figure()
plt.plot(metrics_leach["time"], metrics_leach["delivery_ratio"], label="LEACH")
plt.plot(metrics_heed["time"],  metrics_heed["delivery_ratio"],  label="HEED")
plt.plot(metrics_deecrp["time"],  metrics_deecrp["delivery_ratio"],  label="DEECRP")
plt.xlabel("Time")
plt.ylabel("Delivery Ratio")
plt.title("Delivery Ratio Comparison")
plt.ylim(0, 1)
plt.grid(True)
plt.legend()
plt.show()


plt.figure()
plt.plot(metrics_leach["time"], metrics_leach["alive_nodes"], label="LEACH")
plt.plot(metrics_heed["time"],  metrics_heed["alive_nodes"],  label="HEED")
plt.plot(metrics_deecrp["time"], metrics_deecrp["alive_nodes"], label="DEECRP")

plt.xlabel("Time")
plt.ylabel("Number of Alive Nodes")
plt.title("Alive Nodes Over Time")
plt.grid(True)
plt.legend()
plt.show()


total_nodes = nb_nodes

dead_leach = [total_nodes - a for a in metrics_leach["alive_nodes"]]
dead_heed  = [total_nodes - a for a in metrics_heed["alive_nodes"]]
dead_deecrp = [total_nodes - a for a in metrics_deecrp["alive_nodes"]]

plt.figure()
plt.plot(metrics_leach["time"], dead_leach, label="LEACH")
plt.plot(metrics_heed["time"],  dead_heed,  label="HEED")
plt.plot(metrics_deecrp["time"], dead_deecrp, label="DEECRP")

plt.xlabel("Time")
plt.ylabel("Number of Dead Nodes")
plt.title("Dead Nodes Over Time")
plt.grid(True)
plt.legend()
plt.show()


plt.figure()
plt.plot(metrics_leach["time"],metrics_leach["received_by_bs_ts"],label="LEACH")
plt.plot(metrics_heed["time"],metrics_heed["received_by_bs_ts"],label="HEED")
plt.plot(metrics_deecrp["time"],metrics_deecrp["received_by_bs_ts"],label="DEECRP")

plt.xlabel("Time")
plt.ylabel("Cumulative Data Received at BS")
plt.title("Cumulative Data Delivered to BS")
plt.grid(True)
plt.legend()
plt.show()


plt.figure()
plt.plot(metrics_leach["time"], metrics_leach["energy_total"], label="LEACH")
plt.plot(metrics_heed["time"],  metrics_heed["energy_total"],  label="HEED")
plt.plot(metrics_deecrp["time"], metrics_deecrp["energy_total"], label="DEECRP")

plt.xlabel("Time")
plt.ylabel("Total Energy (J)")
plt.title("Total Network Energy vs Time")
plt.grid(True)
plt.legend()
plt.show()


