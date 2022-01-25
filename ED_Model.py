# imports below
import simpy
import random
from ED_Patient import EDPatient


# start of global class g
# just for test, will probally be deleted later
class g:
    WI_inter = 5
    mean_ctas_assessment = 10
    mean_ed_registration = 6
    mean_bdassig = 7
    mean_treat = 8
    sim_duration = 120
    number_of_runs = 1
    inter = 10


# start of model class
class EDModel:

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
    def generate_walk_in_arrivals(self):
        while True:
            # incrase patient counter
            self.patient_counter +=1

            # create walk-in patient (wp)
            # ED_Patient empty for now
            wp = EDPatient(self.patient_counter)

            # interarrival time for walk-In patients
            # after we create the patient we wait and then the patient arrives at the ED
            ## TO THINK ABOUT IT: I think it is best if we create all the interarrival
            ## times when we create the patient so we can use the patient to call in the number
            ## since for different CTAS we can have different times
            interarrival_for_walkIn = random.expovariate(1.0 / g.WI_inter)
            yield self.env.timeout(interarrival_for_walkIn)

            # after patient is created he enters the ED after some time
            self.env.process(self.emergency_department_process(wp)) # -> problem here

            # wait until you reapeat the process again
            sampled_interarrival = random.expovariate(1.0 / g.inter)
            yield self.env.timeout(sampled_interarrival)

    def generate_ambulance_arrivals(self):
        while True:
            # incrase patient counter
            self.patient_counter += 1

            # create ambulance patient (ab)
            # ED_Patient empty for now
            ab = EDPatient(self.patient_counter)

            # interarrival time for walk-In patients
            # after we create the patient we wait and then the patient arrives at the ED
            ## TO THINK ABOUT IT: I think it is best if we create all the interarrival
            ## times when we create the patient so we can use the patient to call in the number
            ## since for different CTAS we can have different times
            interarrival_for_ambulance = random.expovariate(1.0 / g.WI_inter)
            yield self.env.timeout(interarrival_for_ambulance)

            # after patient is created he enters the ED after some time
            self.env.process(self.emergency_department_process(ab)) # -> problem here

            # wait until you reapeat the process again
            sampled_interarrival = random.expovariate(1.0 / g.inter)
            yield self.env.timeout(sampled_interarrival)

    # Cover from priority assessment to bed assigment
    def emergency_department_process(self, patient):
            # Priority assesment: if patient is CTAS level 1 go to bed assigment and skip the rest
        if patient.CTAS_level == 1:  # patient goes directlly to bed assignment
            # call bed_assignment and activate it with patient
            # bed_assignment empty for now
            # later create special ressucetion bed def
            yield self.env.process(self.bed_assignment(patient))
            pass
        else:  # if not go thought the ED normally
            # call CTAS_assessment and activate it with patient
            yield self.env.process(self.ctas_assessment(patient))

            # call ED_Registration and activate it with patient
            # ED_Registration empty for now
            yield self.env.process(self.ed_registration(patient))

            # call bed_assignment and activate it with patient
            # bed_assignment empty for now
            yield self.env.process(self.bed_assignment(patient))


    # after arriving at hospital patient gets its CTAS assessment
    def ctas_assessment(self,patient):
        # print patient ID an arrival at ED
        print("Patient ", patient.id, " started queueing at ", self.env.now, sep="")

        # request a nurse
        with self.nurse.request() as req:
            # wait until a nurse is avaiable then lock the nurse and continue to the emergency_department_process
            yield req

            print("Patient ", patient.id, " got CTAS nurse at ", self.env.now, sep="")

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse
            sampled_assesment_duration = random.expovariate(1.0 / g.mean_ctas_assessment)
            yield self.env.timeout(sampled_assesment_duration)

    def ed_registration(self,patient):
        # print patient ID an arrival at ED
        print("Patient ", patient.id, " started queueing at registration at ", self.env.now, sep="")

        # request a nurse
        with self.nurse.request() as req:
            # wait until a nurse is avaiable then lock the nurse and continue to the emergency_department_process
            yield req

            print("Patient ", patient.id, " got CTAS nurse at ", self.env.now, sep="")

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse
            sampled_registration_duration = random.expovariate(1.0 / g.mean_ed_registration)
            yield self.env.timeout(sampled_registration_duration)

    def bed_assignment(self,patient):

        with self.regular_beds.request() as req:
            # print patient ID an arrival at ED
            print("Patient ", patient.id, " started queueing at bed_assignment at ", self.env.now, sep="")
            with self.nurse.request() as req2:
                # wait until a nurse and bed is avaiable then lock both
                yield req
                yield req2

                print("Patient ", patient.id, " got bed_assignment nurse at ", self.env.now, sep="")

                # sampled_xxxx_duration is getting a random value from the mean and then
                # is going to wait that time until it concluded and with that releases the nurse but not bed
                sampled_bed_assig_duration = random.expovariate(1.0 / g.mean_bdassig)
                yield self.env.timeout(sampled_bed_assig_duration)

        # release nurse but keep the bed
        # call treatment and activate it with patient
        self.env.process(self.treatment(patient))

    def treatment(self,patient):

        with self.doctor.request() as req:
            # print patient ID an arrival at ED
            print("Patient ", patient.id, " started queueing at treatment at ", self.env.now, sep="")
            with self.nurse.request() as req2:
                # wait until a nurse and doctor is avaiable then lock both
                yield req
                yield req2

                print("Patient ", patient.id, " got treatment at ", self.env.now, sep="")

                # sampled_xxxx_duration is getting a random value from the mean and then
                # is going to wait that time until it concluded and with that releases the nurse and doctor
                sampled_treat_duration = random.expovariate(1.0 / g.mean_treat)
                yield self.env.timeout(sampled_treat_duration)

    def run(self):
        self.env.process(self.generate_walk_in_arrivals())
        self.env.process(self.generate_ambulance_arrivals())
        self.env.run(until=g.sim_duration)


for run in range(g.number_of_runs):
    print ("Run ", run+1, " of ", g.number_of_runs, sep="")
    my_ed_model = EDModel()
    my_ed_model.run()
    print("\n")
