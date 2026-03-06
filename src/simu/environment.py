from simu.sensors import Sensors, State
from simu.base_station import BaseStation
from simu.communications import Communication
from simu.metric import Metric


from simpy.util import start_delayed

import random
from math import dist


class Event:
    def __init__(self, time, x, y, radius):
        self.time = time
        self.x = x
        self.y = y
        self.radius = radius

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
        
    # Dispatch events to all surrounding sensors
    def dispatch_event(self, event: Event):       
      
        for sensor in self.sensors:
            if dist(sensor.position, (event.x, event.y)) <= event.radius and sensor.state != State.DEAD:
                sensor.trigger()
                self.nb_awake += 1
                self.config.environment.metric.event_generated()
          
                
    def is_finished(self):
        for sensor in self.sensors:
            if sensor.state != State.DEAD:
                return False
        return True
    
    # Generate random events for the x next seconds
    def generate_events(self, duration, prob_per_second):
        events = []
        current_time = int(self.simpy_env.now)
        end_time = current_time + duration
        for t in range(current_time + 1, end_time + 1):
            if random.random() < prob_per_second:
                pos_x = random.randint(self.config.min_x, self.config.max_x)
                pos_y = random.randint(self.config.min_y, self.config.max_y)
                r = random.randint(self.config.min_r_event, self.config.max_r_event)
                events.append(Event(t, pos_x, pos_y, r))
                # print(f"Event created at ({pos_x}, {pos_y}) of radius {r} scheduled at {t}")

        return events
    
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
            # Generate events for the next 10 seconds
            upcoming_events = self.generate_events(10, self.config.prob_event_per_second)
            upcoming_events.sort(key=lambda e: e.time)
            for event in upcoming_events:
                time_to_event = event.time - self.simpy_env.now
                if time_to_event > 0:
                    yield simpy_env.timeout(time_to_event)
                    self.dispatch_event(event)
                else:
                    self.dispatch_event(event)
                
            yield simpy_env.timeout(10)

            self.metric.update(simpy_env)

            
        base_station.interrupt()

            
            
