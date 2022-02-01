from os import sep
import random


# ctas _dist should have the from: {1:0.2, 2: 0.3, 3: 0.1, 4:0.1, 5: 0.3}
class Patient:
    p_id = 0
    arrival_time = 0
    los = 0 


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
