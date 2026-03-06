from simu.node import Node
from simu.messsage import Message


import simpy
import random

from enum import Enum

MSG_TYPES = {"DATA", "AGG_DATA", "BASE_STATION"}

class OutOfEnergy(Exception):
    pass

class State(Enum):
    AWAKE = 0
    SLEEP = 1 
    DEAD = 2

class Sensors(Node):
    def __init__(self, position, id, config):
        super().__init__(position, id, config)
        self.state = State.SLEEP
        self.er = config.EI
        self.my_ch = None


        
    def trigger(self):
        if self.state == State.SLEEP:
            self.er -= self.config.E_STARTUP
            self.sleep_event.succeed()
    
    
    def send(self, radio_range, msg):
            length = msg.length
            if radio_range < self.config.d0:
                E = length * self.config.E_TX + length * self.config.E_FS * radio_range**2
            else:
                E = length * self.config.E_TX + length * self.config.E_MP * radio_range**4
            self.er -= E 
            if self.er <= 1e-6:
                raise OutOfEnergy()
            super().send(radio_range, msg)
         

        
    def receive(self, timeout=0):
            msg = yield self.simpy_env.process(super().receive(timeout))

            # AUCUN message reçu
            if msg is None:
                return None
            
            if msg.tag in MSG_TYPES:
                E = msg.length * self.config.E_RX
                self.er -= E
                if self.er <= 0:
                    raise OutOfEnergy()

            return msg

    
    def aggregate(self, timeout=1):
        now = self.simpy_env.now
        aggregates = [0]

        while True:
            remaining = timeout - (self.simpy_env.now - now)
            if remaining <= 0:
                break
                
            msg = yield from self.receive(remaining)
            if msg is None:
                break 
                
            if msg.tag == "DATA":
                self.config.environment.metric.event_received_by_ch()
                aggregates.append(msg.data)
                E = self.config.E_DA * self.config.PACKET_SIZE
                self.er -= E
                if self.er <= 1e-6:
                    raise OutOfEnergy()

        return aggregates
                
    def iteration(self):               
        pass
    
    def end_iteration(self):
        pass
                
    def loop(self):
        try:
            self.sleep_event = self.simpy_env.event()
            last_time = self.simpy_env.now
        
            while True:
                yield self.sleep_event
                self.er -= self.config.E_SLEEP * (self.simpy_env.now - last_time)
                last_time = self.simpy_env.now
                if self.er <= 1e-6:
                    raise OutOfEnergy()
                
                self.state = State.AWAKE
                
                yield from self.iteration()
                self.er -= self.config.E_IDLE * (self.simpy_env.now - last_time)
                last_time = self.simpy_env.now
                if self.er <= 1e-6:
                    raise OutOfEnergy()
                
                if self.my_ch == self.id:
                
                    msgs = yield from self.aggregate(1)
                    self.er -= self.config.E_IDLE * (self.simpy_env.now - last_time)
                    last_time = self.simpy_env.now
                    if self.er <= 1e-6:
                        raise OutOfEnergy()

                    length_total = self.config.PACKET_SIZE * len(msgs)
                    if self.next_hop is None:
                        msg_bs = Message(self.id, self.simpy_env.now, "BASE_STATION", msgs, length_total)
                        self.config.environment.metric.event_sent_by_ch()
                        self.send(self.config.RANGE, msg_bs)
                    else:
                        msg_r = Message(self.id, self.simpy_env.now, "ROUTE_DATA", msgs, length_total)
                        self.send(self.config.RANGE, msg_r)

                else:
                    msg_ch = Message(self.id, self.simpy_env.now, "DATA", {"value": random.randint(1, 100), "my_ch": self.my_ch}, self.config.PACKET_SIZE)
                    self.send(self.config.RANGE, msg_ch)
                
                self.end_iteration()
                
                if self.state == State.SLEEP:
                    self.sleep_event = self.simpy_env.event()
                    last_time = self.simpy_env.now

        except OutOfEnergy:   
            self.state = State.DEAD
            print(f"Node {self.id}: I'm dead")
    
    def main(self, simpy_env):
        self.simpy_env = simpy_env
        self.proc = simpy_env.process(self.loop())

             