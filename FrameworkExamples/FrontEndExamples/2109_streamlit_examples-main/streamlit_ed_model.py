# from numpy.lib.arraysetops import ediff1d
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import ed_sim_simpy_model as ed

#Title
st.title('Emergency Department Simulation')

# File Upload/Processing
file = st.file_uploader('Upload .csv file with data')
def process_file(file):
    st.write(file)
    df = pd.read_csv(file)
    st.write(df)
if st.button('Process file'):
    process_file(file)

#Inputting Fields/ Sliders
col1, col2, col3 = st.columns(3)
col2.subheader('Resource Allocation')
col3.subheader('Patient Inter-Arrival Times')
col1.subheader('Process Service Times')
with col2:
    docs = st.number_input('Number of Doctors', 1, 5, 2)
    nurse = st.number_input('Number of Nurses', 1, 5, 2)
    beds = st.number_input('Number of Beds', 1, 5, 2)
    resbeds = st.number_input('Number of Resuscitation Beds', 1, 5, 2)
with col3:
    walkInP = st.number_input('Walk-In Patients', 1, 1000, 478)
    AmbulanceP = st.number_input('Ambulance Patients', 1, 50, 9)
with col1:
    CTASass = st.number_input('CTAS Assessment', 1, 50, 42)
    Priorityass = st.number_input('Priority Assessment', 1, 50, 23)
    Initialass = st.number_input('Initial Assessment', 1, 50, 42)
    Dischargeass = st.number_input('Discharge Assessment', 1, 50, 23)
    Treatment = st.number_input('Treatments', 1, 50, 20)
    Bedass = st.number_input('Bed Assignment', 1, 50, 32)
    Resus = st.number_input('Resuscitations', 1, 50, 19)
    Registration = st.number_input('Registrations', 1, 50, 49)
st.header('Simulation Parameters')
simPar_duration = st.number_input('Duration', 1, 30, 10)
simPar_iterations = st.number_input('Iterations', 5, 40, 18)
simPar_warmUp = st.number_input('Warm Up Period', 1, 30, 10)

#The graphs being displayed/modeled
model = ed.Model(docs, beds, walkInP)

if st.button('Run Simulation'):
    # Get results
    chart, text = model.run()
    # Show chart
    st.pyplot(chart)
    # Display results (text)
    for t in text:
        st.write(t)


