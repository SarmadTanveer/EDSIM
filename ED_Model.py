# imports below
import simpy
import random
from ED_Patient import Patient
from functools import partial
from Reource_monitor import patch_resource, monitor


# start of global class g
# just for test, will probally be deleted later
class g:
    # means
    WI_inter = 12
    mean_ctas_assessment = 10
    mean_ed_registration = 6
    mean_bdassig = 7
    mean_treat = 8
    sim_duration = 120 # In minutes
    number_of_runs = 1
    inter = 10

    # resource values
    nurse_quantity = 3
    doctor_quantity = 1
    regular_beds_quantity = 1
    resuscitation_beds_quantity = 1
    equipments_quantity = 1

    # CTAS levels percentage
    ctas_dist = {1: 0.2, 2: 0.3, 3: 0.1, 4: 0.1, 5: 0.3}

####### I think that the functions have priority:
####### funnctions that are above one another will run first
####### example if we have one patient queueing at ctas_assigment and another at ressuction_beds_assigment and 1 nurse,
####### the nurse will prioritize the request at ctas_assigment since the function appears first
####### in this case the nurse should have gone to ressuction_beds_assigment since is more important and the patient has a higher ctas level
# start of model class
class EDModel:

    def __init__(self):
        # create enviroment
        self.env = simpy.Environment()

        # set up resources
        self.nurse = simpy.PriorityResource(self.env, capacity=g.nurse_quantity)
        self.doctor = simpy.PriorityResource(self.env, capacity=g.doctor_quantity)
        self.regular_beds = simpy.PriorityResource(self.env, capacity=g.regular_beds_quantity)
        self.resuscitation_beds = simpy.PriorityResource(self.env, capacity=g.resuscitation_beds_quantity)
        self.equipments = simpy.PriorityResource(self.env, capacity=g.equipments_quantity)

    # this generates patients that walked in the ED
    def generate_walk_in_arrivals(self):
        while True:

            # create walk-in patient (wp)
            # when patient is created is when he arrives
            wp = Patient(ctas_dist=g.ctas_dist)

            # after patient is created he enters the ED after some time
            self.env.process(self.emergency_department_process(wp))  # -> problem here

            # interarrival time for walk-In patients
            # after we create the patient we wait and then the patient arrives at the ED
            ## TO THINK ABOUT IT: I think it is best if we create all the interarrival
            ## times when we create the patient so we can use the patient to call in the number
            ## since for different CTAS we can have different times
            interarrival_for_walkIn = random.expovariate(1.0 / g.WI_inter)
            yield self.env.timeout(interarrival_for_walkIn)

    def generate_ambulance_arrivals(self):
        while True:

            # create ambulance patient (ab)
            # when patient is created is when he arrives
            ab = Patient(ctas_dist=g.ctas_dist)

            # after patient is created he enters the ED after some time
            self.env.process(self.emergency_department_process(ab)) # -> problem here

            # interarrival time for ambulance patients
            # after we create the patient we wait and then the patient arrives at the ED
            ## TO THINK ABOUT IT: I think it is best if we create all the interarrival
            ## times when we create the patient so we can use the patient to call in the number
            ## since for different CTAS we can have different times
            interarrival_for_ambulance = random.expovariate(1.0 / g.WI_inter)
            yield self.env.timeout(interarrival_for_ambulance)

    # Cover from priority assessment to bed assigment
    def emergency_department_process(self, patient):
            # Priority assesment: if patient is CTAS level 1 go to bed assigment and skip the rest
        if patient.CTAS_Level == 1:  # patient goes directlly to bed assignment
            # call bed_assignment and activate it with patient
            # bed_assignment empty for now
            # later create special ressucetion bed def
            yield self.env.process(self.resuscitation_bed_assignment(patient))
            pass
        else:  # if not go thought the ED normally
            # call CTAS_assessment and activate it with patient
            yield self.env.process(self.ctas_assessment(patient))

            # call ED_Registration and activate it with patient
            # ED_Registration empty for now
            yield self.env.process(self.ed_registration(patient))

            # call bed_assignment and activate it with patient
            # bed_assignment empty for now
            yield self.env.process(self.regular_bed_assignment(patient))

    # after arriving at hospital patient gets its CTAS assessment
    def ctas_assessment(self,patient):
        # print patient ID and arrival at ED
        patient.set_arrival_time(self.env.now)
        print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " started queueing at ctas_assessment at ", self.env.now, sep="")

        # request a nurse
        with self.nurse.request(priority=patient.CTAS_Level) as req:
            # wait until a nurse is avaiable then lock the nurse and continue to the emergency_department_process
            yield req

            time_to_begin_ctas_assessment = self.env.now - patient.arrival_time
            print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " time differemce to begin ctas assessment: ", time_to_begin_ctas_assessment, " got CTAS nurse at ", self.env.now, sep="")

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse
            sampled_assesment_duration = random.expovariate(1.0 / g.mean_ctas_assessment)
            yield self.env.timeout(sampled_assesment_duration)

    def ed_registration(self,patient):
        # print patient ID an arrival at ED
        print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " started queueing at registration at ", self.env.now, sep="")

        # request a nurse
        with self.nurse.request(priority=patient.CTAS_Level) as req:
            # wait until a nurse is avaiable then lock the nurse and continue to the emergency_department_process
            yield req

            time_to_begin_ed_registration = self.env.now - patient.arrival_time
            print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " time differemce: ", time_to_begin_ed_registration, " got CTAS nurse at ", self.env.now, sep="")

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse
            sampled_registration_duration = random.expovariate(1.0 / g.mean_ed_registration)
            yield self.env.timeout(sampled_registration_duration)

    def regular_bed_assignment(self,patient):

        with self.regular_beds.request(priority=patient.CTAS_Level) as req:
            # print patient ID an arrival at ED
            print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " started queueing at regular_bed_assignment at ", self.env.now, sep="")
            with self.nurse.request(priority=patient.CTAS_Level) as req2:
                # wait until a nurse and bed is avaiable then lock both
                yield req
                yield req2

                time_to_begin_regular_beds = self.env.now - patient.arrival_time
                print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " time differemce: ", time_to_begin_regular_beds, " got bed_assignment nurse at ", self.env.now, sep="")

                # sampled_xxxx_duration is getting a random value from the mean and then
                # is going to wait that time until it concluded and with that releases the nurse but not bed
                sampled_bed_assig_duration = random.expovariate(1.0 / g.mean_bdassig)
                yield self.env.timeout(sampled_bed_assig_duration)

        # release nurse but keep the bed
        # call treatment and activate it with patient
        yield self.env.process(self.treatment(patient))

    def resuscitation_bed_assignment(self,patient):

        with self.resuscitation_beds.request(priority=patient.CTAS_Level) as req:
            # print patient ID an arrival at ED
            print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " started queueing at resuscitation_beds at ", self.env.now, sep="")
            with self.nurse.request(priority=patient.CTAS_Level) as req2:
                # wait until a nurse and bed is avaiable then lock both
                yield req
                yield req2

                time_to_begin_resuscitation_beds = self.env.now - patient.arrival_time
                print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " time differemce: ", time_to_begin_resuscitation_beds, " got bed_assignment nurse at ", self.env.now, sep="")

                # sampled_xxxx_duration is getting a random value from the mean and then
                # is going to wait that time until it concluded and with that releases the nurse but not bed
                sampled_bed_assig_duration = random.expovariate(1.0 / g.mean_bdassig)
                yield self.env.timeout(sampled_bed_assig_duration)

        # release nurse but keep the bed
        # call treatment and activate it with patient
        yield self.env.process(self.treatment(patient))

    def treatment(self,patient):

        with self.doctor.request(priority=patient.CTAS_Level) as req:
            # print patient ID an arrival at ED
            print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " started queueing at treatment at ", self.env.now, sep="")
            with self.nurse.request(priority=patient.CTAS_Level) as req2:
                # wait until a nurse and doctor is avaiable then lock both
                yield req
                yield req2

                time_to_begin_treatment = self.env.now - patient.arrival_time
                print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " time differemce: ", time_to_begin_treatment, " got treatment at ", self.env.now, sep="")

                # sampled_xxxx_duration is getting a random value from the mean and then
                # is going to wait that time until it concluded and with that releases the nurse and doctor
                sampled_treat_duration = random.expovariate(1.0 / g.mean_treat)
                yield self.env.timeout(sampled_treat_duration)
                print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " left at ", self.env.now, sep="")

    def run(self):
        self.env.process(self.generate_walk_in_arrivals())
        self.env.process(self.generate_ambulance_arrivals())
        self.env.run(until=g.sim_duration)

data = []
monitor = partial(monitor, data)
for run in range(g.number_of_runs):
    print ("Run ", run+1, " of ", g.number_of_runs, sep="")
    my_ed_model = EDModel()
    patch_resource(my_ed_model.nurse, post=monitor)  # Patches (only) this resource instance
    my_ed_model.run()
    print("\n")
    print(data)
    # before cleaning the data do the necessary calculations and save it
    data.clear()
