import simpy
import simpy.core
from math import dist

from simu.sensors import State
from simu.base_station import BaseStation

class Communication:
    def __init__(self):
        self.map_nodes_id = {}
        self.map_nodes_store = {}
        
        
    def setup(self, simpy_env):
        self.simpy_env = simpy_env
        
    def get_output_conn(self, node):
        store = simpy.Store(self.simpy_env, capacity=simpy.core.Infinity)
        self.map_nodes_id[node.id] = node
        self.map_nodes_store[node.id] = store 
        return store
            
    def can_receive(self, sender_id, receiver_id, rr):
        sender = self.map_nodes_id[sender_id]
        receiver = self.map_nodes_id[receiver_id]
        return dist(sender.position, receiver.position) <= rr and (isinstance(receiver, BaseStation) or receiver.state == State.AWAKE)
            
            
    def send(self, sender_id, rr, msg):
        for receiver_id in self.map_nodes_id.keys():
            if sender_id != receiver_id:
                if self.can_receive(sender_id, receiver_id, rr):
                    self.map_nodes_store[receiver_id].put(msg)
                    
