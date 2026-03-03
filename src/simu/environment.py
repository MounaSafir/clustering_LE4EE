from simu.sensors import Sensors, State
from simu.base_station import BaseStation
from simu.communications import Communication
from simu.metric import Metric


from simpy.util import start_delayed

import random
from math import dist


class Environment:
    def __init__(self, config):
        self.config = config
        self.sensors = []
        self.metric = Metric(self)
        self.config.environment = self

  


        self.communications = Communication()
        
        # Create sensors
        for i in range(config.nb_sensors):
            sensor = self.config.create_sensor(f"sensor-{i}", config)
            self.sensors.append(sensor)
            
        # Create base station
        self.base_station = BaseStation((config.bs_x, config.bs_y), "bs-0", config)
        self.nb_awake = 0
        
                
        
    
    
    def create_event(self):
        time = random.randint(1, 10)
        yield self.simpy_env.timeout(time)
        pos_x = random.randint(self.config.min_x, self.config.max_x)
        pos_y = random.randint(self.config.min_y, self.config.max_y)
        r = random.randint(self.config.min_r_event, self.config.max_r_event)
       
        print(f"Event created at ({pos_x}, {pos_y}) of radius {r} à {self.simpy_env.now}")
      

        for sensor in self.sensors:
            if dist(sensor.position, (pos_x, pos_y)) <= r and sensor.state != State.DEAD:
                sensor.trigger()
                self.nb_awake += 1
                self.config.environment.metric.event_generated()
          
                
    def is_finished(self):
        for sensor in self.sensors:
            if sensor.state != State.DEAD:
                return False
        return True
    
    def main(self, simpy_env):
        self.simpy_env = simpy_env 
        self.communications.setup(simpy_env)
        self.base_station.setup_communications(self.communications)
        base_station = simpy_env.process(self.base_station.main(simpy_env))
        for sensor in self.sensors:
            sensor.setup_communications(self.communications)
            sensor.main(simpy_env)
                    
        self.metric.update(simpy_env)
        while not self.is_finished():
            
            for i in range(1):
                self.simpy_env.process(self.create_event())
                
            yield simpy_env.timeout(10)

            self.metric.update(simpy_env)

            
        base_station.interrupt()
        print("Fin de la simulation")

            
            
