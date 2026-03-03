from simu.node import Node

import simpy

class BaseStation(Node):
    def __init__(self, position, id, config):
        super().__init__(position, id, config)
        self.position = position
        

    def setup_communications(self, communications):
        self.communications = communications
        self.input_comm = communications.get_output_conn(self)
        
    def main(self, simpy_env):
        self.simpy_env = simpy_env
        try:
            while True:
                msg = yield self.simpy_env.process(self.receive())
                while msg != None:
                    if msg.tag == "BASE_STATION":
                        nb_events = len(msg.data)
                        self.config.environment.metric.event_received_by_bs(nb_events)
                        self.config.environment.metric.event_received_by_bs_ag()
                    msg = yield self.simpy_env.process(self.receive())
                yield self.simpy_env.timeout(1)
        except simpy.exceptions.Interrupt as e:
            return 
                
            