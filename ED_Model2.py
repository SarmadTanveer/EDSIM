# imports below
import simpy
import random
from ED_Patient import Patient, ambulancePatient, walkInPatient
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

    #containers 
    regular_beds_quantity = 1
    resuscitation_beds_quantity = 1
    equipments_quantity = 1

    # CTAS levels percentage
    ctas_dist = {1: 0.2, 2: 0.3, 3: 0.1, 4: 0.1, 5: 0.3}
    codeRed_Prob = 0.5

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

        #priority levels
        self.highPrio = 1
        self.medPrio = 2
        self.lowPrio = 3 

        # set up resources
        self.nurse = simpy.PriorityResource(self.env, capacity=g.nurse_quantity)
        self.doctor = simpy.PriorityResource(self.env, capacity=g.doctor_quantity)
        self.regular_beds = simpy.PriorityResource(self.env, capacity=g.regular_beds_quantity)
        self.resuscitation_beds = simpy.PriorityResource(self.env, capacity=g.resuscitation_beds_quantity)
        self.equipments = simpy.PriorityResource(self.env, capacity=g.equipments_quantity)

    # this generates patients that walked in the ED
    def generate_walk_in_arrivals(self,numPatients):
        for i in range (numPatients): 

            # create walk-in patient (wp)
            # when patient is created is when he arrives
            wp = Patient(ctas_dist=g.ctas_dist)
            print(f"Patient {wp.id} generated with ctas level {wp.CTAS_Level} \n")

            # after patient is created he enters the ED after some time
            self.env.process(self.emergency_department_process(wp))  

            # interarrival time for walk-In patients
            # after we create the patient we wait and then the patient arrives at the ED
            ## TO THINK ABOUT IT: I think it is best if we create all the interarrival
            ## times when we create the patient so we can use the patient to call in the number
            ## since for different CTAS we can have different times
            interarrival_for_walkIn = random.expovariate(1.0 / g.WI_inter)
            yield self.env.timeout(interarrival_for_walkIn)

    # this generates patients that arrived by ambulance in the ed
    def generate_ambulance_arrivals(self, numPatients):
        for i in range (numPatients): 

            # create ambulance patient (ab)
            # when patient is created is when he arrives
            ap = Patient(ctas_dist=g.ctas_dist)
            print(f"Patient {ap.id} generated with ctas level {ap.CTAS_Level} \n")

            # after patient is created he enters the ED after some time
            self.env.process(self.emergency_department_process(ap)) # -> problem here

            # interarrival time for ambulance patients
            # after we create the patient we wait and then the patient arrives at the ED
            ## TO THINK ABOUT IT: I think it is best if we create all the interarrival
            ## times when we create the patient so we can use the patient to call in the number
            ## since for different CTAS we can have different times
            interarrival_for_ambulance = random.expovariate(1.0 / g.WI_inter)
            yield self.env.timeout(interarrival_for_ambulance)

    # Cover from priority assessment to bed assigment
    def emergency_department_process(self, patient):
        
        #walk in patient goes through priority assessment 
        if isinstance(patient, walkInPatient): 
            yield self.env.process(self.priority_assessment(patient))

        #three pathways for ambulance patient
        elif isinstance(patient, ambulancePatient):
            #patient requires resuscitation
            if patient.CTAS_Level == 1: 
                yield self.env.process(self.resuscitation(patient))
            
            #patient is not severe but requires immediate care CTAS 2 and 3
            elif (patient.CTAS_Level == 2 ):
                yield self.env.process(self.bed_assignment(patient))

            #patient is not severe and can proceed normally through the ed 4 and 5
            else: 
                yield self.env.process(self.registration(patient)) 
            

        
    
    # Priority assessment Code red or blue 
    def priority_assessment(self, patient):
        #patient enters queue  
        arrival = self.env.now
        print(f"Patient {patient.id} has entered the priority assessment queue at {arrival} mins \n")

        with self.nurse.request(priority=self.highPrio) as req: 
            #wait till nurse is available 
            yield req 

            #nurse is available and patient can be seen by nurse
            print(f"Patient {patient.id} has left the priority assessment queue at {self.env.now} \n")
            
            #this is how long the patient waited for the nurse 
            wait = self.env.now - arrival

            #nurse takes time to assess 
            sampled_service_time = random.expovariate(1.0/g.mean_ctas_assessment)
            yield self.env.timeout(sampled_service_time)

        if patient.CTAS_Level == 1: 
            #add patient to resuscitation queue 
            self.env.process(self.resuscitation())
            
        elif(patient.CTAS_level == 2):
            #add patienti to bed assignment queue
            self.env.process(self.bed_assignment(patient))
        else: 
            #add patient to ctas queue 
            self.env.process(self.ctas_assessment(patient))



    # after priority assessment patient gets ctas assessed
    def ctas_assessment(self,patient):
        #patient enters queue  
        arrival = self.env.now
        print(f"Patient {patient.id} has entered the ctas assessment queue at {arrival} mins \n")

        # request a nurse
        with self.nurse.request(priority=patient.CTAS_Level) as req:
            # wait until a nurse is avaiable then lock the nurse and continue to the emergency_department_process
            yield req

            print(f"Patient {patient.id} has left the ctas assessment queue at {self.env.now} \n")
            
            #this is how long the patient waited for the nurse 
            wait = self.env.now - arrival

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse
            sampled_service_time = random.expovariate(1.0 / g.mean_ctas_assessment)
            yield self.env.timeout(sampled_service_time)
        #add patient to registration queue i.e waiting area 1 
        self.env.process(self.registration(patient)) 

    def registration(self,patient):
        #patient enters queue  
        arrival = self.env.now
        print(f"Patient {patient.id} has entered the registration queue at {arrival} mins \n")

        # request a nurse
        with self.nurse.request(priority=patient.CTAS_Level) as req:
            # wait until a nurse is avaiable then lock the nurse and continue to the emergency_department_process
            yield req

            print(f"Patient {patient.id} has left the registration queue at {self.env.now} \n")
            
            #this is how long the patient waited for the nurse 
            wait = self.env.now - arrival

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse
            sampled_service_time = random.expovariate(1.0 / g.mean_ed_registration)
            yield self.env.timeout(sampled_service_time)
        #add patient to bed assignment queue i.e waiting area 2
        self.env.process(self.bed_assignment(patient))

    def bed_assignment(self,patient):
         #patient enters queue  
        arrival = self.env.now
        print(f"Patient {patient.id} has entered the bed assignment queue at {arrival} mins \n")

        bed_request = self.regular_beds.request(priority=patient.CTAS_Level)
        yield bed_request

        #bed is available and has been locked 
        print(f"Bed is availble at {self.env.now} \n")
        wait_for_bed = self.env.now - arrival 

        print("Waiting for nurse \n")
        #request a nurse 
        with self.nurse.request(priority=patient.CTAS_Level) as req:
                # wait until a nurse and bed is avaiable then lock both
                yield req

                #nurse is available 
                wait = self.env.now - arrival

                print(f"Patient {patient.id} has left the bed assignment queue at {self.env.now}")

                # sampled_xxxx_duration is getting a random value from the mean and then
                # is going to wait that time until it concluded and with that releases the nurse but not bed
                sampled_service_time = random.expovariate(1.0 / g.mean_bdassig)
                yield self.env.timeout(sampled_service_time)
        self.env.process(self.initial_assessment(patient))

        # release nurse but keep the bed
        # call treatment and activate it with patient
        yield self.env.process(self.treatment(patient))

    def resuscitation(self,patient):

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
    
    #Initial Assessment: 
    def initial_assessment(self, patient):
        arrival = self.env.now
        print(f"Patient {patient.id} has entered the initial assessment queue at {arrival} mins \n")

        with self.nurse.request(priority=self.lowPrio) as req, self.doctor.request(priority=patient.CTAS_Level) as req2: 
            #wait till nurse is available 
            yield req 
            #wait till doctor is avaialble 
            yield req 
            
            print(f"Patient {patient.id} has left the initial assessment queue at {self.env.now} \n")
            wait = self.env.now - arrival

            sampled_service_time = random.expovariate(1.0/g.mean_ctas_assessment)
            yield self.env.timeout(sampled_service_time)
        self.env.process(self.treatment(patient))
#---> left here 
    #Treatment: 
    def treatment(self,patient):
        arrival = self.env.now
        print(f"Patient {patient.id} has entered the treatment queue at {arrival} mins \n")

        with self.doctor.request(priority=patient.CTAS_Level) as req:
            # doctor is available 
            print(f"Doctor is avialble \n")
            with self.nurse.request(priority=patient.CTAS_Level) as req2:
                # wait until a nurse and doctor is avaiable then lock both
                yield req
                yield req2

                print(f"Patient {patient.id} has left the treatment queue at {self.env.now} \n")
                wait = self.env.now - arrival

                # sampled_xxxx_duration is getting a random value from the mean and then
                # is going to wait that time until it concluded and with that releases the nurse and doctor
                sampled_treat_duration = random.expovariate(1.0 / g.mean_treat)
                yield self.env.timeout(sampled_treat_duration)
                print("Patient ", patient.id, " CTAS:", patient.CTAS_Level, " left at ", self.env.now, sep="")
    
    #Discharge Decision
    def discharge_decision(self, patient): 
        arrival = self.env.now 
        print(f"Patient: {patient.id} has entered the discharge queue at {arrival} \n")

        sampled_service_time = random.expovariate(1/g.mean_ctas_assessment)

        yield self.env.timeout(sampled_service_time)
        print(f"Patient: {patient.id} has left the ed at {self.env.now}\n")
    
    
    
    def run(self):
        self.env.process(self.generate_walk_in_arrivals(1))
        #self.env.process(self.generate_ambulance_arrivals(1))
        self.env.run()

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
