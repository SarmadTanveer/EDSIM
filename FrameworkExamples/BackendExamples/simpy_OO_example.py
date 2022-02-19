import simpy 
import random 

class g: 
    wl_inter = 5
    mean_consult = 6
    number_of_nurses = 1
    sim_duration = 120
    number_of_runs = 10

class Weight_loss_Patient:
    def __init__(self,p_id):
        self.id = p_id
    
class GP_Surgery_Model:
    def __init__(self):
        self.env = simpy.Environment()
        self.patient_counter = 0

        self.nurse = simpy.Resource(self.env, capacity=g.number_of_nurses)

    def generate_wl_arrivals(self):

        while True:
            self.patient_counter +=1

            wp = Weight_loss_Patient(self.patient_counter)

            self.env.process(self.attend_wl_clinic(wp))

            sampled_interarrival = random.expovariate(1.0/g.wl_inter)

            yield self.env.timeout(sampled_interarrival)
    
    def attend_wl_clinic(self, patient):
        yield self.env.process(self.registration(self.nurse, patient))
        yield self.env.process(self.consultation(patient, self.nurse))
           
        
    def run(self):
        self.env.process(self.generate_wl_arrivals())

        self.env.run(until=g.sim_duration)
    
    def consultation(self, patient, nurse):
        print("Patient ", patient.id, " started queueing for cons at ", self.env.now, sep="")

        with nurse.request() as req:
            
            yield req
        
            print("Patient ", patient.id, " finished queueing for cons at ", self.env.now, sep="")

            sampled_cons_duration = random.expovariate(1.0/g.mean_consult)

            yield self.env.timeout(sampled_cons_duration)
    
    def registration(self, nurse, patient):
        print("Patient ", patient.id, " started queueing for reg at ", self.env.now, sep="")

        with nurse.request() as req:
            
            yield req
        
            print("Patient ", patient.id, " finished queueing for reg at ", self.env.now, sep="")

            sampled_registration_duration = random.expovariate(1.0/g.mean_consult)

            yield self.env.timeout(sampled_registration_duration)
        

for run in range(g.number_of_runs):
    print ("Run ", run+1, " of ", g.number_of_runs, sep="")
    my_gp_model = GP_Surgery_Model()
    my_gp_model.run()
    print("\n")