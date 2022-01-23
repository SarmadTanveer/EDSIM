#Data class to hold simulation parameters
class Data:
    def __init__(self, simParameters):
        #resource capacities 
        self.doctorCap = simParameters['resCapacity']['doctor']
        self.nurseCap = simParameters['resCapacity']['nurse']
        self.bedCap = simParameters['resCapacity']['beds']

        #service times
        self.rBedCap = simParameters['resCapacity']['rBeds']
        self.pInterAmbulance = simParameters['pInterArrival']['ambulance']
        self.pInterWalkIn = simParameters['pInterArrival']['walkIn']
        self.arrAssessmentMean = simParameters['serTimes']['arrAssessment']
        self.bedAssessmentMean = simParameters['serTimes']['bedAssignment']
        self.ctasAssessment = simParameters['serTimes']['ctasAssessment']
        self.discharge = simParameters['serTimes']['discharge']
        self.initAssessment = simParameters['serTimes']['initAssessment']
        self.registration = simParameters['serTimes']['resuscitation']
        self.treatment = simParameters['serTimes']['treatment']
        
        #ctas distribution - ambulance
        self.ambulanceCtas1 = simParameters['ambulance'][1]
        self.ambulanceCtas2 = simParameters['ambulance'][2]
        self.ambulanceCtas3 = simParameters['ambulance'][3]
        self.ambulanceCtas4 = simParameters['ambulance'][4]
        self.ambulanceCtas5 = simParameters['ambulance'][5] 

        #ctas distribution - walkin 
        self.walkInCtas1 = simParameters['ambulance'][1]
        self.walkInCtas2 = simParameters['ambulance'][2]
        self.walkInCtas3 = simParameters['ambulance'][3]
        self.walkInCtas4 = simParameters['ambulance'][4]
        self.walkInCtas5 = simParameters['ambulance'][5]

        #Number of iterations 
        self.iterations = simParameters['iter']

        #Warm up Period
        self.iterations = simParameters['warmUp']

        #Length of Sim
        self.length = simParameters['length']