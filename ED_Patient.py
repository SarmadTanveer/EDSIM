import simpy
import random


class EDPatient:

    def __init__(self, id):
        # set up patient information
        self.id = id
        self.CTAS_level = 3