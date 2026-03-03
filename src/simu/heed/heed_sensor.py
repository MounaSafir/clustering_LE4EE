import random
from math import dist
from simu.messsage import Message
from simu.sensors import Sensors, State


class HeedSensors(Sensors):

    def __init__(self, position, id, config):
        super().__init__(position, id, config)

        self.C_prob = 0.1        
        
        self.p_min = 0.01

        self.is_tentative_ch = False
        self.is_final_ch = False


    def iteration(self):
        self.next_hop = None
        self.is_tentative_ch = False
        self.is_final_ch = False 
        self.my_ch = None

        ch_proba = max (self.C_prob * (self.er / self.config.EI),self.p_min)

        for _ in range(3):
            if not self.is_tentative_ch and not self.is_final_ch:
                

                if random.random() < ch_proba:
                    self.is_tentative_ch = True

            if self.is_tentative_ch:
                msg = Message(
                    self.id,
                    self.simpy_env.now,
                    "CH_ADV",
                    self.position,
                    100
                )
                self.send(self.config.RANGE, msg)

            yield self.simpy_env.timeout(0.1)

            msg = yield from self.receive(3)
            best_ch = None
            best_dist = float("inf")

            while msg is not None:
                if msg.tag == "CH_ADV":
                    d = dist(self.position, msg.data)
                    if d < best_dist:
                        best_dist = d
                        best_ch = msg.sender
                msg = yield from self.receive(3)

            if self.is_tentative_ch and best_ch == self.id:
                self.is_final_ch = True
                self.my_ch = self.id
                break
                
            if best_ch is not None:
                self.my_ch = best_ch
            
            ch_proba = min(2*ch_proba, 1.0)


            if self.my_ch is None:
                self.is_final_ch = True
                self.my_ch = self.id

    def end_iteration(self):
        self.state = State.SLEEP
