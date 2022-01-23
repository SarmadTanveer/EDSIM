import simpy
import random

# start of model class
class ED_Model:

    def __init__(self):
        # create enviroment
        self.env = simpy.Environment()
        # set up initial values
        self.patient_counter = 0
        self.nurse = simpy.Resource(self.env, capacity=1)
        self.doctor = simpy.Resource(self.env, capacity=1)