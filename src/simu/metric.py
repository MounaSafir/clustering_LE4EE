from simu.sensors import State


class Metric:
    def __init__(self, environment):
        self.env = environment

        self.data = {
            "time": [],
            "energy_total": [],
            "energy_avg": [],
            "alive_nodes": [],
            "generated_events" : 0,
            "received_by_ch": 0,
            "sent_by_ch":0,
            "received_by_bs":0,
            "received_by_bs_ag":0 ,
            "delivery_ratio": [],
 
            "received_by_bs_ts": [],
        
            
        }

        self.nb_nodes = len(environment.sensors)

    def update(self, simpy_env):
     
        alive_nodes = [
            node for node in self.env.sensors
            if node.state != State.DEAD
        ]

        if alive_nodes:
            total_energy = sum(node.er for node in alive_nodes)
            avg_energy = total_energy / len(alive_nodes)
        else:
            total_energy = 0
            avg_energy = 0

        self.data["time"].append(simpy_env.now)
        self.data["energy_total"].append(total_energy)
        self.data["energy_avg"].append(avg_energy)
        self.data["alive_nodes"].append(len(alive_nodes))

        self.data["received_by_bs_ts"].append(
        self.data["received_by_bs"]
    )

        gen = self.data["generated_events"]
        rec = self.data["received_by_bs"]

        if gen > 0:
            dr = rec / gen
        else:
            dr = 0

        self.data["delivery_ratio"].append(dr)






    def event_generated(self):
        self.data["generated_events"] += 1

    def event_received_by_ch(self):
        self.data["received_by_ch"] += 1

    def event_sent_by_ch(self):
        self.data["sent_by_ch"] += 1

    def event_received_by_bs(self,nb_events):
        self.data["received_by_bs"] += nb_events


    def event_received_by_bs_ag(self):
        self.data["received_by_bs_ag"] += 1



    def print_delivery_ratio(self):
        gen = self.data["generated_events"]
        rec = self.data["received_by_bs"]

        if gen > 0:
            dr = rec / gen
        else:
            dr = 0

        print(f"Delivery ratio = {dr:.4f} ({dr*100:.2f}%)")
