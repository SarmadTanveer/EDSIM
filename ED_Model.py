# imports below
import simpy
import random

# start of model class
class ED_Model:

    def __init__(self):
        # create enviroment
        self.env = simpy.Environment()

        # set up initial values
        self.patient_counter = 0

        # set up resources
        self.nurse = simpy.Resource(self.env, capacity=1)
        self.doctor = simpy.Resource(self.env, capacity=1)
        self.regular_beds = simpy.Resource(self.env, capacity=1)
        self.resuscitation_beds = simpy.Resource(self.env, capacity=1)
        self.equipments = simpy.Resource(self.env, capacity=1)

    # this generates patients that walked in the ED
    def generate_walkIn_arrivals(self):
        while True:
            # incrase patient counter
            self.patient_counter +=1

            # create walk-in patient (wp)
            # ED_Patient empty for now
            wp = ED_Patient(self.patient_counter)

            # interarrival time for walk-In patients
            # after we create the patient we wait and then the patient arrives at the ED
            ## TO THINK ABOUT IT: I think it is best if we create all the interarrival
            ## times when we create the patient so we can use the patient to call in the number
            ## since for different CTAS we can have different times
            interarrival_for_walkIn = random.expovariate(1.0 / g.WI_inter)
            yield self.env.timeout(interarrival_for_walkIn)

            # after patient is created he enters the ED after some time
            self.env.process(self.arrive_at_ED(wp))

    def generate_ambulance_arrivals(self):
        while True:
            # incrase patient counter
            self.patient_counter += 1

            # create ambulance patient (ab)
            # ED_Patient empty for now
            ab = ED_Patient(self.patient_counter)

            # interarrival time for walk-In patients
            # after we create the patient we wait and then the patient arrives at the ED
            ## TO THINK ABOUT IT: I think it is best if we create all the interarrival
            ## times when we create the patient so we can use the patient to call in the number
            ## since for different CTAS we can have different times
            interarrival_for_ambulance = random.expovariate(1.0 / g.WI_inter)
            yield self.env.timeout(interarrival_for_ambulance)

            # after patient is created he enters the ED after some time
            self.env.process(self.arrive_at_ED(ab))

    def arrive_at_ED(self, patient):
            # Priority assesment: if patient is CTAS level 1 go to bed assigment and skip the rest
        if patient.CTAS_level == 1:  # patient goes directlly to bed assignment
            # call bed_assignment and activate it with patient
            # bed_assignment empty for now
            self.env.process(self.bed_assignment(patient))
            # call treatment and activate it with patient
            # treatment empty for now
            self.env.process(self.treatment(patient))
            pass
        else:  # if not go thought the ED normally
            # call CTAS_assessment and activate it with patient
            # CTAS_assessment empty for now
            self.env.process(self.CTAS_assessment(patient))

            # call ED_Registration and activate it with patient
            # ED_Registration empty for now
            self.env.process(self.ED_Registration(patient))

            # call bed_assignment and activate it with patient
            # bed_assignment empty for now
            self.env.process(self.bed_assignment(patient))

            # call treatment and activate it with patient
            # treatment empty for now
            self.env.process(self.treatment(patient))




