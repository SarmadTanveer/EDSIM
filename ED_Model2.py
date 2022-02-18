# imports below
import simpy
import random
from ED_Patient import Patient, ambulancePatient, walkInPatient
from functools import partial
from Reource_monitor import patch_resource, monitor
import pandas as pd

class Writer: 
    

    def ConvertToDataFrame(runList):
        
        patientData = pd.DataFrame(runList)
        print(patientData)
        print(patientData.columns)
        print(patientData.shape)
        print(patientData.dtypes)
        print(patientData.describe())
        return patientData
       
    #def addPatientToLOS(self, patient):
    #def addPatientiToRQT(self,patient):
    #def getAllData(self):
    #def cleanFrame(self):
    def writeToCsv(patientData, name):
        patientData.to_csv(name,index = False)

    #def calcAvgPatientsPerRun(patientData): 

    #def getNumPatientsByCTAS(patientData): 

    #def getAvgLOS(patientData): 

    

    #def getData(Name): 

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
        self.warmUp = simParameters['warmUp']

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
        
        #initial parameters
        self.parameters = parameters

        #list of patients during this run 
        self.patientList = []
        self.resourceMonitor = []
        self.resuscitationBedWait = []


    # this generates patients that walked in the ED
    def generate_walk_in_arrivals(self,numPatients):
        #while True:
        for i in range (numPatients): 

            # create walk-in patient (wp)
            # when patient is created is when he arrives
            wp = walkInPatient(ctas_dist=self.parameters.walkInCtas)
            #print(f"Walk in Patient {wp.id} generated with ctas level {wp.CTAS_Level} \n")

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
            #print(f"Ambulance Patient {ap.id} generated with ctas level {ap.CTAS_Level} \n")

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

        # Take the arrival time here because all patients pass through here so it is easier
        patient.arrival_time = self.env.now

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
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the priority assessment queue at {arrival} mins")


        with self.nurse.request(priority=self.highPrio) as req: 
            #wait till nurse is available 
            yield req 

            #nurse is available and patient can be seen by nurse
            #print(f"Patient {patient.id} with CTAS level has left the priority assessment queue at {self.env.now}  mins")

            #this is how long the patient waited for the nurse
            patient.priority_assessment_time = self.env.now  # do we really need a set function?
            PQT = patient.priority_assessment_time - patient.arrival_time
            #print(f"Patient {patient.id} waited {PQT} mins for the nurse")

            #this is how we save queing time in the patient class 
            #patient.PQT['priorAssessment'] = PQT

            #nurse takes time to assess 
            sampled_service_time = random.expovariate(1.0/self.parameters.priorAssessment)
            yield self.env.timeout(sampled_service_time)

        patient.priority_assessment_time_end = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has gone through priority assessment at {self.env.now} mins")

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
        patient.ctas_assessment_time_arrival = self.env.now
        arrival = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the ctas assessment queue at {arrival} mins")

        # request a nurse
        with self.nurse.request(priority=patient.CTAS_Level) as req:
            # wait until a nurse is avaiable then lock the nurse and continue to the emergency_department_process
            yield req

            #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the ctas assessment queue at {self.env.now} mins")
            
            #this is how long the patient waited for the nurse 
            patient.ctas_assessment_time = self.env.now
            PQT = patient.ctas_assessment_time - patient.ctas_assessment_time_arrival
            #print(f"Patient {patient.id} waited {PQT} mins for the nurse")

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse
            sampled_service_time = random.expovariate(1.0 / self.parameters.ctasAssessment)
            yield self.env.timeout(sampled_service_time)
        patient.ctas_assessment_time_end = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has gone through CTAS assessment at {self.env.now} mins")

        #add patient to registration queue i.e waiting area 1 
        self.env.process(self.registration(patient)) 

    def registration(self,patient):
        #patient enters queue
        patient.registration_time_arrival = self.env.now
        arrival = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the registration queue at {arrival} mins")

        # request a nurse
        with self.nurse.request(priority=patient.CTAS_Level) as req:
            # wait until a nurse is avaiable then lock the nurse and continue to the emergency_department_process
            yield req

            #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the registration queue at {self.env.now} mins")
            
            #this is how long the patient waited for the nurse 
            patient.registration_time = self.env.now
            PQT = patient.registration_time - patient.registration_time_arrival
            #print(f"Patient {patient.id} waited {PQT} mins for the nurse")

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse
            sampled_service_time = random.expovariate(1.0 / self.parameters.registration)
            yield self.env.timeout(sampled_service_time)
        patient.registration_time_end = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has gone through registration at {self.env.now} mins")
        #add patient to bed assignment queue i.e waiting area 2
        self.env.process(self.bed_assignment(patient))

    def bed_assignment(self,patient):
        #patient enters queue
        patient.bed_assignment_time_arrival = self.env.now
        arrival = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the bed assignment queue at {arrival} mins")

        bed_request = self.regular_beds.request(priority=patient.CTAS_Level)
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} is waiting for bed")
        yield bed_request

        patient.bed = bed_request

        #bed is available and has been locked 
        #print(f"Bed is availble at {self.env.now} for Patient {patient.id} with CTAS level {patient.CTAS_Level}")
        
        #resource queueing time: regular bed
        patient.bed_assignment_time_bed = self.env.now
        RQT = patient.bed_assignment_time_bed - patient.bed_assignment_time_arrival
        #patient.rqt['regularbed'] = RQT

        #request a nurse 
        with self.nurse.request(priority=patient.CTAS_Level) as req:
                # wait until a nurse and bed is avaiable then lock both
                yield req

                #nurse is available 
                patient.bed_assignment_time_nurse = self.env.now
                PQT = patient.bed_assignment_time_nurse - patient.bed_assignment_time_arrival
                #print(f"Patient {patient.id} waited {PQT} mins for the nurse")

                #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the bed assignment queue at {self.env.now} mins")

                # sampled_xxxx_duration is getting a random value from the mean and then
                # is going to wait that time until it concluded and with that releases the nurse but not bed
                sampled_service_time = random.expovariate(1.0 / self.parameters.bedAssignment)
                yield self.env.timeout(sampled_service_time)
        patient.bed_assignment_time_end = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has been assigned a bed at {self.env.now} mins")
        self.env.process(self.initial_assessment(patient))

    
    #have to modify this
    def resuscitation(self,patient):
        patient.resuscitation_time_arrival = self.env.now
        arrival = self.env.now
        
        # print patient ID an arrival at ED
        #print(f"Patien {patient.id} with CTAS level {patient.CTAS_Level} has entered resuscitation queue at {self.env.now} mins")
        with self.resuscitation_beds.request(priority=0) as req: 
            yield req

            #resuscitation bed acquired
            patient.resuscitation_time_bed = self.env.now
            rBed_queue_time = patient.resuscitation_time_bed - patient.resuscitation_time_arrival
            with self.nurse.request(priority=0) as req1:
                    # wait until a nurse and bed is avaiable then lock both
                yield req1

                with self.doctor.request(priority=0) as req2:

                    yield req2
                    #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the resuscitation queue at {self.env.now} mins" )
                    patient.resuscitation_time_nurse_doctor = self.env.now
                    PQT = patient.registration_time - patient.resuscitation_time_arrival
                    #print(f"Patient {patient.id} waited {PQT} mins for the nurse and doctor")
                
                    # sampled_xxxx_duration is getting a random value from the mean and then
                    # is going to wait that time until it concluded and with that releases the nurse but not bed
                    sampled_service_time = random.expovariate(1.0 / self.parameters.resuscitation)
                    yield self.env.timeout(sampled_service_time)
        patient.resuscitation_time_end = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has gone through resuscitation at {self.env.now} mins")

        ######### error in resuscitation
        ######### Why is a CTAS 1 patient going back to bed assigment? It does not follows the models and mess with the output
        ######### bed_assignmen queue time for ctas level 1 should be zero
        ######### should go to initial_assessment
        self.env.process(self.bed_assignment(patient))
    
    #Initial Assessment: 
    def initial_assessment(self, patient):

        patient.initial_assessment_time_arrival = self.env.now
        #arrival = self.env.now
        #print(self.env.now)
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the initial assessment queue at {arrival} mins")

        with self.doctor.request(priority=patient.CTAS_Level) as req:
            # wait for doctor
            yield req

            #print(self.env.now)
            #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the initial assessment queue at {self.env.now} mins")
            patient.initial_assessment_time_doctor = self.env.now
            #PQT = patient.initial_assessment_time_doctor - patient.initial_assessment_time_arrival
            #print(f"Patient {patient.id} waited {PQT} mins for the doctor")

            sampled_service_time = random.expovariate(1.0/self.parameters.initialAssessment)
            yield self.env.timeout(sampled_service_time)

        #print('end ')
        #print(self.env.now)
        patient.initial_assessment_time_end = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has gone through initial assessment at {self.env.now} mins")
        self.env.process(self.treatment(patient))

    #Treatment: 
    def treatment(self,patient):
        patient.treatment_time_arrival = self.env.now
        #arrival = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the treatment queue at {arrival} mins")

        with self.nurse.request(priority=patient.CTAS_Level) as req:
            # wait until a nurse is available
            yield req

            #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the treatment queue at {self.env.now} mins")
            patient.treatment_time_nurse_doctor = self.env.now
            #PQT = patient.treatment_time_nurse_doctor - patient.treatment_time_arrival
            #print(f"Patient {patient.id} waited {PQT} mins for the nurse and doctor")

            # sampled_xxxx_duration is getting a random value from the mean and then
            # is going to wait that time until it concluded and with that releases the nurse and doctor
            sampled_service_time = random.expovariate(1.0 / self.parameters.treatment)
            yield self.env.timeout(sampled_service_time)
        patient.treatment_time_end = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has been treated at {self.env.now} mins")
        self.env.process(self.discharge_decision(patient))        
    
    #Discharge Decision
    def discharge_decision(self, patient):
        patient.discharge_decision_time_arrival = self.env.now
        #arrival = self.env.now
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has entered the discharge queue at {arrival} mins")

        sampled_service_time = random.expovariate(1/self.parameters.discharge)

        yield self.env.timeout(sampled_service_time)

        # for every 24 hours we save the mean as a data point
        self.regular_beds.release(patient.bed)
        #print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} has left the ed at {self.env.now} mins")

        patient.discharge_decision_time_leaving = self.env.now
        patient.calculate_Times()

        print(f"Patient {patient.id} with CTAS level {patient.CTAS_Level} and type {type(patient)}; initial_assessment_wt {patient.initial_assessment_wt} ")
        print(f"Patient {patient.id} ; initial_assessment_time_doctor {patient.initial_assessment_time_doctor} - initial_assessment_time_arrival {patient.initial_assessment_time_arrival}")

        self.patientList.append(patient.convertToDict())

        
    
    
    def snapshot(self):
       while self.env.peek() < (self.parameters.length+self.parameters.warmUp):
            self.resourceMonitor.append({'Time Stamp': self.env.now, 
                                        'Nurse Queue Length':len(self.nurse.queue),
                                        'Doctor Queue Length': len(self.doctor.queue), 
                                        'Regular Bed Queue Length': len(self.regular_beds.queue), 
                                        'Resuscitation Bed Queue Length': len(self.resuscitation_beds.queue)
                                        }) 
            prevPatientList = self.patientList.copy()
            yield self.env.timeout(5)
            


    def run(self):

        self.env.process(self.generate_walk_in_arrivals(50))
        self.env.process(self.generate_ambulance_arrivals(50))
        self.env.process(self.snapshot())
        self.env.run()
        return (self.patientList, self.resourceMonitor, self.resuscitationBedWait)

def runSim(simParameters):
    parameters = Data(simParameters)
    runList = []
    timeSeries = []
    for run in range(parameters.iterations):
        print('--------------------------------------------------------------------------------')
        print("Run ", run + 1, " of ", parameters.iterations, sep="")
        ed_model = EDModel(parameters)
        patientList,timeList,resuscitationWait = ed_model.run()
        runList.extend(patientList)
        timeSeries.extend(timeList)
        
        
        
        #print(runList)
        Patient.p_id = 0
        Patient.run_id += 1
        print('--------------------------------------------------------------------------------')
        #ed model.run(until=parameters.length)
    print(timeSeries)
    df = Writer.ConvertToDataFrame(runList=runList)
    df2 = Writer.ConvertToDataFrame(timeSeries)
    Writer.writeToCsv(df,"PatientData.csv")
    Writer.writeToCsv(df2,"SnapShotData.csv")
simParameters = {
    'resCapacity': {
        'doctor':1, 
        'nurse':3,
        'beds':25,
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
        'initialAssessment':30,
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
    'iter':5,
    'warmUp':0, 
    'length':300
}

runSim(simParameters)


