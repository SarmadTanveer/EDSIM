import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import Statistics as s

# Done in back-end
class Global_vars:
    """Storage object for global variables."""

    def __init__(self, docs=2, inter_arrival=10, appointment_time=18):
        
        self.appointment_time_mean = appointment_time
        self.appointment_time_sd = self.appointment_time_mean / 2
        self.audit_time = []
        self.audit_interval = 100
        self.audit_patients_in_ED = []
        self.audit_patients_waiting = []
        self.audit_patients_waiting_p1 = []
        self.audit_patients_waiting_p2 = []
        self.audit_patients_waiting_p3 = []
        self.audit_reources_used = []
        self.inter_arrival_time = inter_arrival
        self.number_of_docs = docs
        self.patient_count = 0
        self.patients_waiting = 0
        self.patients_waiting_by_priority = [0, 0, 0]
        self.patient_queuing_results = (pd.DataFrame(
            columns=['priority', 'q_time', 'consult_time']))
        self.results = pd.DataFrame()
        self.sim_duration = 5000
        self.warm_up = 1000

# Done in back-end
class Model:
    """ The model object holds the model and the methods directly relevant to the model."""
    
    def __init__(self, docs, inter_arrival, appointment_time):
        """Creates instances of Global variable and SimPy model environemnt"""

        self.global_vars = Global_vars(docs, inter_arrival, appointment_time)
        self.env = simpy.Environment()

    # Change values to match back-end
    def build_audit_results(self):
        """Compiles audit results into dataframe held in Glov_vars"""
        
        self.global_vars.results['time'] = self.global_vars.audit_time
        
        self.global_vars.results['patients in ED'] = (
            self.global_vars.audit_patients_in_ED)
        
        self.global_vars.results['all patients waiting'] = (
            self.global_vars.audit_patients_waiting)
        
        self.global_vars.results['priority 1 patients waiting'] = (
            self.global_vars.audit_patients_waiting_p1)
        
        self.global_vars.results['priority 2 patients waiting'] = (
            self.global_vars.audit_patients_waiting_p2)
        
        self.global_vars.results['priority 3 patients waiting'] = (
            self.global_vars.audit_patients_waiting_p3)
        
        self.global_vars.results['resources occupied'] = (
            self.global_vars.audit_reources_used)

    #Mean LOS dataframe for each CTAS level
    def los_chart(self, meanLOS):
        meanLOSforCTAS1 = s.getDataByCTASLevel(meanLOS, 1)
        meanLOSforCTAS2 = s.getDataByCTASLevel(meanLOS, 2)
        meanLOSforCTAS3 = s.getDataByCTASLevel(meanLOS, 3)
        meanLOSforCTAS4 = s.getDataByCTASLevel(meanLOS, 4)
        meanLOSforCTAS5 = s.getDataByCTASLevel(meanLOS, 5)

        fig, axs = plt.subplots(5,figsize=(10,17))
        
        # Subplot for each CTAS level
        axs[0].plot(meanLOSforCTAS1, 'C0')
        axs[0].set_xlabel('Run ID')
        axs[0].set_ylabel('Mean length of stay (min)')
        axs[0].set_title('Mean Patient Length of Stay per Run ID (CTAS 1-5)')

        axs[1].plot(meanLOSforCTAS2, 'C1')
        axs[1].set_xlabel('Run ID')
        axs[1].set_ylabel('Mean length of stay (min)')

        axs[2].plot(meanLOSforCTAS3, 'C2')
        axs[2].set_xlabel('Run ID')
        axs[2].set_ylabel('Mean length of stay (min)')

        axs[3].plot(meanLOSforCTAS4, 'C3')
        axs[3].set_xlabel('Run ID')
        axs[3].set_ylabel('Mean length of stay (min)')

        axs[4].plot(meanLOSforCTAS5, 'C4')
        axs[4].set_xlabel('Run ID')
        axs[4].set_ylabel('Mean length of stay (min)')

        return fig
        

    # Done in back-end
    def perform_audit(self):
        """Monitors modelled ED at regular intervals (as defined by audit 
        interval in self.global_vars)"""

        # Delay before first aurdit if length of warm-up
        yield self.env.timeout(self.global_vars.warm_up)
        # The trigger repeated audits
        while True:
            # Record time
            self.global_vars.audit_time.append(self.env.now)
            # Record patients waiting by referencing global variables
            self.global_vars.audit_patients_waiting.append(self.global_vars.patients_waiting)
            
            (self.global_vars.audit_patients_waiting_p1.append
             (self.global_vars.patients_waiting_by_priority[0]))
            
            (self.global_vars.audit_patients_waiting_p2.append
             (self.global_vars.patients_waiting_by_priority[1]))
            
            (self.global_vars.audit_patients_waiting_p3.append
             (self.global_vars.patients_waiting_by_priority[2]))
            
            # Record patients waiting by asking length of dictionary of all patients 
            # (another way of doing things)
            self.global_vars.audit_patients_in_ED.append(len(Patient.all_patients))
            # Record resources occupied
            self.global_vars.audit_reources_used.append(self.doc_resources.docs.count)
            # Trigger next audit after interval
            yield self.env.timeout(self.global_vars.audit_interval)

    def run(self):
        """Runs the model: Sets up resources, initialises model process, and starts
        running the model environment. At the end of the run raw model data is saved
        to file, and summary figure and results are displayed."""
        
        # Set up resources
        self.doc_resources = Resources(self.env, self.global_vars.number_of_docs)
        
        # Initialise processes that will run on model run
        self.env.process(self.trigger_admissions())
        self.env.process(self.perform_audit())
        # Run
        self.env.run(until=self.global_vars.sim_duration)
        
        # End of simulation run. Build and save results.
        # The saved results are the raw audit data
        self.build_audit_results()

        #Read dataframe from csv
        results_df = s.read_csv()

        #Group dataframe by Run ID and CTAS Level
        means = s.meanByGroup(results_df)

        #Mean LOS of grouped dataframe
        meanLOS = s.meanParByCTASperRun(means,'los')

        # Get LOS chart for each CTAS level
        los_chart_output = self.los_chart(meanLOS)

        # Get text summary of results
        text_output = self.summarise()

        return los_chart_output, text_output

    # Done in back-end
    def see_doc(self, p):
        """Mangages waiting for doctor resorce. Records time waiting to see doc""" 
        
        with self.doc_resources.docs.request(priority=p.priority) as req:
            self.global_vars.patients_waiting += 1
            # Wait for resources to become available
            yield req
            # Resources now available
            # Reduce patients waiting counts
            self.global_vars.patients_waiting_by_priority[p.priority - 1] -= 1
            self.global_vars.patients_waiting -= 1
            # Record queuing times in patient object and Global dataframe
            p.time_see_doc = self.env.now
            p.queuing_time = self.env.now - p.time_in
            _results = [p.priority, p.queuing_time]
            yield self.env.timeout(p.consulation_time)
            _results.append(self.env.now - p.time_see_doc)
            # Record results if warm-up complete
            if self.env.now >= self.global_vars.warm_up:
                self.global_vars.patient_queuing_results.loc[p.id] = _results
             # Delete patient (removal from patient dictionary removes only
            # reference to patient and Python then automatically cleans up)
            del Patient.all_patients[p.id]

    # Change values to match back-end
    def summarise(self):
        """Produces displayed text summary of model run"""
        
        # For each patient calaculate time in system as time in queue + time with doc
        self.global_vars.patient_queuing_results['system_time'] =  (
                self.global_vars.patient_queuing_results['q_time'] +
                self.global_vars.patient_queuing_results['consult_time'])
        
        # Put text in string to return
        text = []
        text.append('PATIENT-CENTERED METRICS:')
        text.append ('Lower quartile time in system by priority:')
        text.append (self.global_vars.patient_queuing_results.groupby('priority').quantile(0.25))
        text.append ('Median time in system by priority:')
        text.append (self.global_vars.patient_queuing_results.groupby('priority').quantile(0.50))
        text.append ('Upper quartile time in system by priority:')
        text.append (self.global_vars.patient_queuing_results.groupby('priority').quantile(0.75))
        text.append ('Maximum time in system by priority:')
        text.append (self.global_vars.patient_queuing_results.groupby('priority').quantile(1))
        text.append('---')
        text.append ('ED-CENTRED METRICS:')
        text.append (self.global_vars.results.describe().drop('time', axis=1))

        return text
    
    # Done in back-end
    def trigger_admissions(self):
        """Produces patient arrivals. Initialises a patient object (from Patient class), 
        passes the patient over to the see_doc method, and sets the next admission
        time/event"""
        
        # While loop continues generating new patients
        while True:
            # Initialise new patient (pass environment to be used to record
            # current simulation time)
            p = Patient(self.env, self.global_vars)
            # Add patient to dictionary of patients
            Patient.all_patients[p.id] = p
            # Pass patient to see_doc method
            self.env.process(self.see_doc(p))
            # Sample time for next asmissions
            next_admission = random.expovariate(1 / self.global_vars.inter_arrival_time)
            # Schedule next admission
            yield self.env.timeout(next_admission)

# Done in back-end
class Patient:
    """Class of patient objects. The class also holds a list of all patient objects in 
    all_patients dictionary"""
        
    # The following dictionaries store patients
    all_patients = {}

    # New patient instance
    def __init__(self, env, global_vars):
        self.global_vars =global_vars
        self.global_vars.patient_count += 1
        
        self.consulation_time = (
            random.normalvariate(self.global_vars.appointment_time_mean,
                                 self.global_vars.appointment_time_sd))
        
        self.consulation_time = 0 if self.consulation_time < 0 else self.consulation_time
        self.id = self.global_vars.patient_count
        self.priority = random.randint(1, 3)
        self.queuing_time = 0
        self.time_in = env.now
        self.time_see_doc = 0
        self.time_out = 0
        # 1 is subtracted from priority to align priority (1-3) with zero indexed list (0-2)
        self.global_vars.patients_waiting_by_priority[self.priority - 1] += 1

# Done in back-end
class Resources:
    """Resources required by processes in the model.
    Just holds doctors as the only limiting resorce"""
    
    def __init__(self, env, number_of_docs):
        self.docs = simpy.PriorityResource(env, capacity=number_of_docs)

       


    
