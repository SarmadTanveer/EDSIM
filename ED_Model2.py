# imports below
import simpy
import random
from ED_Patient import Patient, ambulancePatient, walkInPatient
from functools import partial
from Reource_monitor import patch_resource, monitor


# start of global class g
# just for test, will probally be deleted later
class Data:
    def __init__(self, simParameters):
        #resource capacities 
        self.doctorCap = simParameters['resCapacity']['doctor']
        self.nurseCap = simParameters['resCapacity']['nurse']
        self.bedCap = simParameters['resCapacity']['beds']
        self.rBedCap = simParameters['resCapacity']['rBeds']

        #interarrival times
        self.pInterAmbulance = simParameters['pInterArrival']['ambulance']
        self.pInterWalkIn = simParameters['pInterArrival']['walkIn']

        #service times
        self.priorAssessment = simParameters['serTimes']['priorAssessment']
        self.bedAssignment = simParameters['serTimes']['bedAssignment']
        self.ctasAssessment = simParameters['serTimes']['ctasAssessment']
        self.discharge = simParameters['serTimes']['discharge']
        self.initialAssessment = simParameters['serTimes']['initialAssessment']
        self.registration = simParameters['serTimes']['registration']
        self.treatment = simParameters['serTimes']['treatment']
        self.resuscitation = simParameters['serTimes']['resuscitation']
        
        #ctas distribution - ambulance
        self.ambulanceCtas = simParameters['ctasDist']['ambulance']

        #ctas distribution - walkin 
        self.walkInCtas = simParameters['ctasDist']['walkIn']

        #Number of iterations 
        self.iterations = simParameters['iter']

        #Warm up Period
        self.iterations = simParameters['warmUp']

        #Length of Sim
        self.length = simParameters['length']

####### I think that the functions have priority:
####### funnctions that are above one another will run first
####### example if we have one patient queueing at ctas_assigment and another at ressuction_beds_assigment and 1 nurse,
####### the nurse will prioritize the request at ctas_assigment since the function appears first
####### in this case the nurse should have gone to ressuction_beds_assigment since is more important and the patient has a higher ctas level

# start of model class
class EDModel:

    def __init__(self,parameters):
        # create enviroment
        self.env = simpy.Environment()

        #priority levels
        self.highPrio = 1
        self.medPrio = 2
        self.lowPrio = 3 

        # set up resources
        self.nurse = simpy.PriorityResource(self.env, capacity=parameters.nurseCap)
        self.doctor = simpy.PriorityResource(self.env, capacity=parameters.doctorCap)
        self.regular_beds = simpy.PriorityResource(self.env, capacity=parameters.bedCap)
        self.resuscitation_beds = simpy.PriorityResource(self.env, capacity=parameters.rBedCap)
        
        self.parameters = parameters


    # this generates patients that walked in the ED
    def generate_walk_in_arrivals(self,numPatients):
        #while True:
        for i in range (numPatients): 

            # create walk-in patient (wp)
            # when patient is created is when he arrives
            wp = walkInPatient(ctas_dist=self.parameters.walkInCtas)
            print(f"Walk in Patient {wp.id} generated with ctas level {wp.CTAS_Level} \n")

            # after patient is created he enters the ED after some time
            self.env.process(self.emergency_department_process(wp))  

            # interarrival time for walk-In patients
            # after we create the patient we wait and then the patient arrives at the ED
            ## TO THINK ABOUT IT: I think it is best if we create all the interarrival
            ## times when we create the patient so we can use the patient to call in the number
            ## since for different CTAS we can have different times
            interarrival_for_walkIn = random.expovariate(1.0 / self.parameters.pInterWalkIn)
            yield self.env.timeout(interarrival_for_walkIn)

    # this generates patients that arrived by ambulance in the ed
    def generate_ambulance_arrivals(self, numPatients):
        #While
        for i in range (numPatients): 

            # create ambulance patient (ab)
            # when patient is created is when he arrives
            ap = ambulancePatient(ctas_dist=self.parameters.ambulanceCtas)
            print(f"Ambulance Patient {ap.id} generated with ctas level {ap.CTAS_Level} \n")

            # after patient is created he enters the ED after some time
            self.env.process(self.emergency_department_process(ap)) # -> problem here

            # interarrival time for ambulance patients
            # after we create the patient we wait and then the patient arrives at the ED
            ## TO THINK ABOUT IT: I think it is best if we create all the interarrival
            ## times when we create the patient so we can use the patient to call in the number
            ## since for different CTAS we can have different times
            interarrival_for_ambulance = random.expovariate(1.0 / self.parameters.pInterAmbulance)
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
            
            #patient is not severe but requires immediate care CTAS 2 
            elif (patient.CTAS_Level == 2 ):
                yield self.env.process(self.bed_assignment(patient))

            #patient is not severe and can proceed normally through the ed 3,4 and 5
            else: 
                yield self.env.process(self.registration(patient)) 
            

        
    
    # Priority assessment Code red or blue 
    def priority_assessment(self, patient):
        #patient enters queue  
        arrival = self.env.now
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the priority assessment queue at {arrival} mins")

        with self.nurse.request(priority=self.highPrio) as req: 
            #wait till nurse is available 
            yield req 

            #nurse is available and patient can be seen by nurse
            print(f"Patient {patient.id} with CTAS level has left the priority assessment queue at {self.env.now}  mins")
            
            #this is how long the patient waited for the nurse 
            PQT = self.env.now - arrival

            #this is how we save queing time in the patient class 
            #patient.PQT['priorAssessment'] = PQT

            #nurse takes time to assess 
            sampled_service_time = random.expovariate(1.0/self.parameters.priorAssessment)
            yield self.env.timeout(sampled_service_time)
        
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has gone through priority assessment at {self.env.now} mins")

        if patient.CTAS_Level == 1: 
            #add patient to resuscitation queue 
            self.env.process(self.resuscitation(patient))
            
        elif(patient.CTAS_Level == 2):
            #add patienti to bed assignment queue
            self.env.process(self.bed_assignment(patient))
        else: 
            #add patient to ctas queue 
            self.env.process(self.ctas_assessment(patient))



    # after priority assessment patient gets ctas assessed
    def ctas_assessment(self,patient):
        #patient enters queue  
        arrival = self.env.now
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the ctas assessment queue at {arrival} mins")

        # request a nurse
        with self.nurse.request(priority=patient.CTAS_Level) as req:
            # wait until a nurse is avaiable then lock the nurse and continue to the emergency_department_process
            yield req

            print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the ctas assessment queue at {self.env.now} mins")
            
            #this is how long the patient waited for the nurse 
            PQT = self.env.now - arrival

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse
            sampled_service_time = random.expovariate(1.0 / self.parameters.ctasAssessment)
            yield self.env.timeout(sampled_service_time)
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has gone through CTAS assessment at {self.env.now} mins")

        #add patient to registration queue i.e waiting area 1 
        self.env.process(self.registration(patient)) 

    def registration(self,patient):
        #patient enters queue  
        arrival = self.env.now
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the registration queue at {arrival} mins")

        # request a nurse
        with self.nurse.request(priority=patient.CTAS_Level) as req:
            # wait until a nurse is avaiable then lock the nurse and continue to the emergency_department_process
            yield req

            print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the registration queue at {self.env.now} mins")
            
            #this is how long the patient waited for the nurse 
            PQT = self.env.now - arrival

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse
            sampled_service_time = random.expovariate(1.0 / self.parameters.registration)
            yield self.env.timeout(sampled_service_time)
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has gone through registration at {self.env.now} mins")
        #add patient to bed assignment queue i.e waiting area 2
        self.env.process(self.bed_assignment(patient))

    def bed_assignment(self,patient):
         #patient enters queue  
        arrival = self.env.now
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the bed assignment queue at {arrival} mins")

        bed_request = self.regular_beds.request(priority=patient.CTAS_Level)
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} is waiting for bed")
        yield bed_request

        patient.bed = bed_request

        #bed is available and has been locked 
        print(f"Bed is availble at {self.env.now} for Patient {patient.id} with CTAS level {patient.CTAS_Level}")
        
        #resource queueing time: regular bed  
        RQT = self.env.now - arrival 
        #patient.rqt['regularbed'] = RQT

        #request a nurse 
        with self.nurse.request(priority=patient.CTAS_Level) as req:
                # wait until a nurse and bed is avaiable then lock both
                yield req

                #nurse is available 
                PQT = self.env.now - arrival

                print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the bed assignment queue at {self.env.now} mins")

                # sampled_xxxx_duration is getting a random value from the mean and then
                # is going to wait that time until it concluded and with that releases the nurse but not bed
                sampled_service_time = random.expovariate(1.0 / self.parameters.bedAssignment)
                yield self.env.timeout(sampled_service_time)
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has been assigned a bed at {self.env.now} mins")
        self.env.process(self.initial_assessment(patient))

    
    #have to modify this
    def resuscitation(self,patient):
        arrival = self.env.now
        
        # print patient ID an arrival at ED
        print(f"Patien {patient.id} with CTAS level {patient.CTAS_Level} has entered resuscitation queue at {self.env.now} mins")
        with self.resuscitation_beds.request(priority=0) as req: 
            yield req

            #resuscitation bed acquired
            rBed_queue_time = self.env.now - arrival 
            with self.nurse.request(priority=0) as req1:
                    # wait until a nurse and bed is avaiable then lock both
                yield req1

                with self.doctor.request(priority=0) as req2:

                    yield req2
                    print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the resuscitation queue at {self.env.now} mins" )
                    PQT = self.env.now - arrival
                
                    # sampled_xxxx_duration is getting a random value from the mean and then
                    # is going to wait that time until it concluded and with that releases the nurse but not bed
                    sampled_service_time = random.expovariate(1.0 / self.parameters.resuscitation)
                    yield self.env.timeout(sampled_service_time)
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has gone through resuscitation at {self.env.now} mins")
        self.env.process(self.bed_assignment(patient))
    
    #Initial Assessment: 
    def initial_assessment(self, patient):
        arrival = self.env.now
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the initial assessment queue at {arrival} mins")

        with self.doctor.request() as req: 
            #wait for doctor 
            yield req
            
            print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the initial assessment queue at {self.env.now} mins")
            PQT = self.env.now - arrival

            sampled_service_time = random.expovariate(1.0/self.parameters.initialAssessment)
            yield self.env.timeout(sampled_service_time)
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has gone through initial assessment at {self.env.now} mins")
        self.env.process(self.treatment(patient))

    #Treatment: 
    def treatment(self,patient):
        arrival = self.env.now
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the treatment queue at {arrival} mins")

        with self.nurse.request(priority=patient.CTAS_Level) as req:
            # wait until a nurse is available
            yield req

            print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the treatment queue at {self.env.now} mins")
            PQT = self.env.now - arrival

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse and doctor
            sampled_service_time = random.expovariate(1.0 / self.parameters.treatment)
            yield self.env.timeout(sampled_service_time)
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has been treated at {self.env.now} mins")
        self.env.process(self.discharge_decision(patient))        
    
    #Discharge Decision
    def discharge_decision(self, patient): 
        arrival = self.env.now 
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the discharge queue at {arrival} mins")

        sampled_service_time = random.expovariate(1/self.parameters.discharge)

        yield self.env.timeout(sampled_service_time)

        self.regular_beds.release(patient.bed)
        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the ed at {self.env.now} mins")
        LOS = self.env.now - arrival
    
    #snapshot evey 5 minutes
    #def snapshot(self):
     #   while True:
      #      yield self.env.timeout(5)
       #     print(f"Resource Queues: \nNurse: {self.nurse.queue} \nDoctor: {self.doctor.queue} \nBed: {self.regular_beds.queue} \nrBed: {self.resuscitation_beds.queue}")
    
    def run(self):
        self.env.process(self.generate_walk_in_arrivals(10))
        self.env.process(self.generate_ambulance_arrivals(10))
        #self.env.process(self.snapshot())
        self.env.run()



def runSim(simParameters):
    parameters = Data(simParameters)
    print("Run 1")
    ed_model = EDModel(parameters)
    ed_model.run()
    #ed model.run(until=parameters.length)

simParameters = {
    'resCapacity': {
        'doctor':1, 
        'nurse':1, 
        'beds':1, 
        'rBeds':1, 

    }, 
    'pInterArrival':{
        'ambulance':15, 
        'walkIn': 8

    }, 
    'serTimes':{
        'priorAssessment': 5, 
        'ctasAssessment':4, 
        'registration':10, 
        'bedAssignment':10,
        'initialAssessment':20,  
        'treatment':60, 
        'discharge':10,
        'resuscitation':20 
    }, 
    'ctasDist':{
        'ambulance': {
             1:0.5, 
             2:0.2, 
             3:0.3, 
             4:0.1, 
             5:0
            
        }, 
        'walkIn':{
             1:0.3, 
             2:0.2, 
             3:0.1, 
             4:0.1, 
             5:0.1
        }

    }, 
    'iter':1, 
    'warmUp':0, 
    'length':20
}

runSim(simParameters)


