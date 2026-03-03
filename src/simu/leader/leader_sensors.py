from simu.node import Node
from simu.messsage import Message
from simu.sensors import Sensors
from simu.sensors import State, OutOfEnergy


import simpy

class LeaderSensors(Sensors):
    def __init__(self, position, id, config):
        super().__init__(position, id, config)
        
        
    def iteration(self):               
        # Flood everyone
        msg_bully = Message(self.id, self.simpy_env.now, "BULLY_LEADER", None, 1000) #Create the message
        self.send(30, msg_bully) # send it
        
        id_leader = self.id 
        msg = yield from self.receive(1) 
        while msg != None:
            if id_leader < msg.sender and msg.tag == "BULLY_LEADER":
                id_leader = msg.sender 
                self.print(f"My new leader is : {id_leader}")
            msg = yield from self.receive(1)
            
        self.my_ch = id_leader
                
        self.print(f"My leader is : {id_leader}")
        
    
    def end_iteration(self):
        self.state = State.SLEEP
    
             