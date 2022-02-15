
import pandas as pd


def read_csv(): 
    df = pd.read_csv('data.csv')
    print(df)
    print(df.dtypes)
    print(df.groupby(['Run ID']).size().mean())
    return df

def calculateSummary(dataframe): 

    avgNumPatientsPerRun = dataframe.groupby(['Run ID']).size().mean()
    

    summary = {'Avg Patients per Run':1, 
                'Avg Queuing Times': { 

                },
                'Avg Resource Queuing Times':2, 
                'BottleNeck':3 
                }

read_csv()

