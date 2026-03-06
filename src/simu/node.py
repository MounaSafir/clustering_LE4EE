from enum import Enum
import random



class Node:
    
    def __init__(self, position, id, config):
        self.position = position
        self.id = id 
        self.config = config
        
    def print(self, msg):
        print(f"[{self.id}][{self.simpy_env.now}] {msg}")
        
    def setup_communications(self, communications):
        self.communications = communications
        self.input_comm = communications.get_output_conn(self)
        
        
    def send(self, radio_range, msg):
        self.communications.send(self.id, radio_range, msg)

    def receive(self, timeout = 0):
        if timeout == 0:
            if len(self.input_comm.items) == 0:
                return None
            return (yield self.input_comm.get())
        else:
            get_ev = self.input_comm.get()
            to_ev = self.simpy_env.timeout(timeout)
            res = yield get_ev | to_ev

            if get_ev in res:
                return res[get_ev]
            else:
                get_ev.cancel()
                return None    
        
    def trigger(self):
        pass 
    
    def metrics(self):
        pass 
    
    def main(self, simpy_env):
        self.simpy_env = simpy_env
        while True:
            # if random.random() < 0.5 and self.id == 3:
            #     self.print(f"J'envoi un message")
            #     self.send(1000, "Coucou")
            # msg = yield simpy_env.process(self.receive(1))
            # if msg is not None:
            #     self.print(f"J'ai reçu un message" + str(msg))
            yield simpy_env.timeout(1)
        