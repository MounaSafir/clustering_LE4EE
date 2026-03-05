from math import sqrt

class Config:
    def __init__(self, create_sensor):
        
        # Map of the environment
        self.min_x = -100
        self.max_x = 100
        self.min_y = -100
        self.max_y = 100
        self.bs_x = 0
        self.bs_y = 0
        self.nb_sensors = 10

        self.create_sensor = create_sensor         
        # Generation of events
        self.min_r_event = 10
        self.max_r_event = 100
        
        # Energy
        self.E_TX = 50e-9
        self.E_RX = 50e-9
        self.E_DA = 5e-9
        self.E_FS = 10e-12
        self.E_MP = 0.0013e-12
        self.EI = 0.5

        
        # Packet size 
        self.PACKET_SIZE = 4000


        # Computed variables
        self.d0 = sqrt(self.E_FS/self.E_MP)

        self.RANGE = 30


        # DEECRP config

        self.m = 0.2
        self.E_AN = 1

        self.AREA_DIAMETER = sqrt(100**2 + 100**2
        )
 
  