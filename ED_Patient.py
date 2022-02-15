from os import sep
import random


# ctas _dist should have the from: {1:0.2, 2: 0.3, 3: 0.1, 4:0.1, 5: 0.3}
class Patient:
    # Variables
    p_id = 0  # Patient ID
    run_id = 1  # Run ID

    # Exact times
    # Simulation time in minutes
    arrival_time = 0  # Patient arrival time at ED

    priority_assessment_time = 0  # time when patient received the resources in priority_assessment
    priority_assessment_time_end = 0  # time when patients leaves priority_assessment

    ctas_assessment_time_arrival = 0  # time when entered ctas assessment
    ctas_assessment_time = 0  # time when patient received the resources in ctas_assessment
    ctas_assessment_time_end = 0  # time when patients leaves ctas_assessment

    registration_time_arrival = 0  # time when entered registration
    registration_time = 0   # time when patient received the resources in registration
    registration_time_end = 0  # time when patients leaves registration

    bed_assignment_time_arrival = 0  # time when entered bed_assignment
    bed_assignment_time_bed = 0  # time when patient received the bed resource in bed_assignment
    bed_assignment_time_nurse = 0  # time when patient received the nurse resource in bed_assignment
    bed_assignment_time_end = 0  # time when patients leaves bed_assignment

    resuscitation_time_arrival = 0   # time when entered resuscitation
    resuscitation_time_bed = 0  # time when patient received the bed resource in resuscitation
    resuscitation_time_nurse_doctor = 0  # time when patient received the nurse and doctor resource in resuscitation
    resuscitation_time_end = 0  # time when patients leaves resuscitation

    initial_assessment_time_arrival = 0  # time when entered initial_assessment
    initial_assessment_time_doctor = 0  # time when patient received the doctor resource in initial_assessment
    initial_assessment_time_end = 0  # time when patients leaves initial_assessment

    treatment_time_arrival = 0  # time when entered treatment
    treatment_time_nurse_doctor = 0  # time when patient received the nurse and doctor resource in treatment
    treatment_time_end = 0  # time when patients leaves treatment

    discharge_decision_time_arrival = 0 # time when entered discharge_decision
    discharge_decision_time_leaving = 0  # time when left discharge_decision and exited the model

    # Calculated times
    los = 0  # Patient lenght of stay

    priority_assessment_wt = 0  # total time patient waited the resources in priority_assessment
    priority_assessment_total_time = 0  # total time patient was in priority_assessment

    ctas_assessment_wt = 0  # total time patient waited the resources in ctas_assessment
    ctas_assessment_total_time = 0  # total time patient was in ctas_assessment

    registration_wt = 0  # total time patient waited the resources in registration
    registration_total_time = 0  # total time patient was in registration

    bed_assignment_wt_bed = 0  # total time patient waited the bed resource in bed_assignment
    bed_assignment_wt_nurse = 0  # total time patient waited the nurse resource in bed_assignment
    bed_assignment_time = 0  # total time patient was in bed_assignment

    resuscitation_wt_bed = 0  # total time patient waited the bed resource in resuscitation
    resuscitation_wt_nurse_doctor = 0  # total time patient waited the nurse and doctor resource in resuscitation
    resuscitation_time = 0  # total time patient was in resuscitation

    initial_assessment_wt = 0  # total time patient waited the resources in initial_assessment
    initial_assessment_total_time = 0  # total time patient was in initial_assessment

    treatment_wt = 0  # total time patient waited the resources in treatment
    treatment_total_time = 0  # total time patient was in treatment

    discharge_decision_total_time = 0  # total time patient was in discharge_decision

    def __init__(self, ctas_dist):
        self.id = self.p_id
        self.CTAS_Level = self.setCTAS(ctas_dist)
        Patient.p_id += 1

    # Output a CTAS level depending on ctas distribution provided by user
    def setCTAS(self, ctas_dist):
        
        # generate a random number between 0 and 1
        sample = random.uniform(0,1)
        ctas_level = 5
        
        # assign ctas_level on likelyhood of random number being between certain limits
        # sample<=0.2 = 20% chance
        if(sample <= ctas_dist[1]):
            ctas_level = 1
        # sample>0.2 and sample <=0.5 = 30 % chance
        elif(sample > ctas_dist[1] and sample<= (ctas_dist[1] + ctas_dist[2]) ):
            ctas_level = 2
        elif(sample> (ctas_dist[1] + ctas_dist[2]) and sample <= (ctas_dist[1] + ctas_dist[2] + ctas_dist[3])): 
            ctas_level = 3
        elif(sample>(ctas_dist[1]+ctas_dist[2]+ ctas_dist[3]) and sample<=(ctas_dist[1]+ctas_dist[2] +ctas_dist[3] + ctas_dist[4])):
            ctas_level = 4
        
        return ctas_level
    
    #Output if the patient is code red i.e needs resuscitation 

    def set_arrival_time(self, arrival_time):
        self.arrival_time = arrival_time

    # Do all necessary calculations
    def calculate_Times(self):
        self.los = self.discharge_decision_time_leaving - self.arrival_time

        self.priority_assessment_wt = self.priority_assessment_time - self.arrival_time
        self.priority_assessment_total_time = self.priority_assessment_time_end - self.arrival_time

        self.ctas_assessment_wt = self.ctas_assessment_time - self.ctas_assessment_time_arrival
        self.ctas_assessment_total_time = self.ctas_assessment_time_end - self.ctas_assessment_time_arrival

        self.registration_wt = self.registration_time - self.registration_time_arrival
        self.registration_total_time = self.registration_time_end - self.registration_time_arrival

        
        self.bed_assignment_wt_bed = self.bed_assignment_time_bed - self.bed_assignment_time_arrival
        self.bed_assignment_wt_nurse = self.bed_assignment_time_nurse - self.bed_assignment_time_bed
        self.bed_assignment_time_wt = self.bed_assignment_wt_bed + self.bed_assignment_wt_nurse
        self.bed_assignment_time = self.bed_assignment_time_end - self.bed_assignment_time_arrival

        self.resuscitation_wt_bed = self.resuscitation_time_bed - self.bed_assignment_time_arrival
        self.resuscitation_wt_nurse_doctor = self.resuscitation_time_nurse_doctor - self.resuscitation_time_bed
        self.resuscitation_time_wt = self.resuscitation_wt_bed + self.resuscitation_wt_nurse_doctor
        self.resuscitation_time = self.resuscitation_time_end - self.resuscitation_time_arrival

        self.initial_assessment_wt = self.initial_assessment_time_doctor - self.initial_assessment_time_arrival
        self.initial_assessment_total_time = self.initial_assessment_time_end - self.initial_assessment_time_arrival

        self.treatment_wt = self.treatment_time_nurse_doctor - self.treatment_time_arrival
        self.treatment_total_time = self.treatment_time_end - self.treatment_time_arrival

        self.discharge_decision_total_time = self.discharge_decision_time_leaving - self.discharge_decision_time_arrival

    def convertToDict(self):
        data = {'Patient ID': self.id, 
                'Run ID': self.run_id, 
                'CTAS': self.CTAS_Level, 
                'Type': "ambulance" if isinstance(self, ambulancePatient) else "walkin", 
                'Arrival': self.arrival_time, 
                'los': self.los, 
                'Priority Assessment Queue Time ': self.priority_assessment_wt, 
                'CTAS Assessment Queue Time': self.ctas_assessment_wt, 
                'Registration Queue Time': self.registration_wt, 
                'Bed Assignment Queue Time': self.bed_assignment_time_wt, 
                'Resuscitation Queue Time': self.resuscitation_time_wt,  
                'Initial Assessment Queue Time': self.initial_assessment_wt, 
                'Treatment Queue Time': self.treatment_wt, 
                'Discharge Time': self.discharge_decision_total_time, 

                'Resuscitation Bed Queueing Time': self.resuscitation_wt_bed, 
                'Resuscitation Queing Nurse/Doctor': self.resuscitation_time_nurse_doctor, 


                'Bed Assignment Queue for Nurse': self.bed_assignment_wt_nurse, 
                'Bed Assignment Queue for Bed': self.bed_assignment_wt_bed 
        }

        return data
class walkInPatient(Patient):

    def __init__(self, ctas_dist):
        # set other properties 
        
        # call super 
        super().__init__(ctas_dist)

class ambulancePatient(Patient):
    def __init__(self, ctas_dist):
        # call super
        super().__init__(ctas_dist)

#Pateint Test
#ctas_dist = {1:0.2, 2: 0.3, 3: 0.1, 4:0.1, 5: 0.3}

#for i in range (0,1):
    #wp = walkInPatient(ctas_dist)
    #print("CTAS level for walkin pateint ", wp.id, " : ", wp.CTAS_Level, sep = "")
    #print(isinstance(wp, walkInPatient))
#for i in range(0,100):
#    ap = ambulancePatient(ctas_dist)
#    print("CTAS level for ambulance patient ", ap.id, " : ",ap.CTAS_Level, sep="")
