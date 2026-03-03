import random
from math import dist
from simu.messsage import Message
from simu.sensors import Sensors, State


class LeachSensors(Sensors):

    def __init__(self, position, id, config):
        super().__init__(position, id, config)
       
        self.p = 0.1
        self.is_ch = False

    def iteration(self):
      
        self.is_ch = False
        self.my_ch = None
        self.next_hop = None
     

    
        if random.random() < self.p:
            self.is_ch = True
            self.my_ch = self.id
            #self.print("I AM CH")
            
            msg = Message(
                self.id,
                self.simpy_env.now,
                "CH_ADV",
                self.position,
                100
            )
            self.send(self.config.RANGE, msg)

        
        

        msg = yield from self.receive(3)
        best_ch = None
        best_dist = float("inf")

        while msg is not None:
            if msg.tag == "CH_ADV":
                d = dist(
                    self.position, msg.data
                )
                if d < best_dist:
                    best_dist = d
                    best_ch = msg.sender
            
            #print(f"I am {self.id}",f"{ best_ch} is my CH")
            msg = yield from self.receive(3)

       
        if not self.is_ch:
            if best_ch is not None:
                self.my_ch = best_ch
       

      
    def end_iteration(self):
        self.state = State.SLEEP
