#!/usr/bin/env python
# coding: utf-8

# # Calibration - SPOTPY
# ## Juncal Norte - august, 2022
# #### Paul Sandoval Quilodrán - https://github.com/SQPaul

# #### import packages

# In[1]:


import subprocess
import os
import time
import numpy as np
import pandas as pd
import openpyxl
import datetime
import spotpy
from configparser import ConfigParser


# In[ ]:


class sphy_model(object):

    def __init__(self):
        
        return

    def get_obs(self):
        
        obs_path = r"C:\Users\pauls\Desktop\Proyectos\Juncal_norte\Caudales\qobs_v1.csv"
        obs = pd.read_csv(obs_path)
        obs = obs.iloc[:,1]
        obs = obs.values
        
        self.observations = obs

        return 

    def run_sphy(self,DDFG=None,DDFDG=None,TCrit=None,DDFS=None,kx=None):
        
        #Read config_file
        config_path = r"C:\juncal_norte\TEST_sphy_config_juncal_norte.cfg" 
        config_jnorte = ConfigParser()
        config_jnorte.read(config_path)

        params_to_iterate = [DDFG,DDFDG,TCrit,DDFS,kx] #vector with param values        
        
        #Change the param values in the config file THE MAGIC!!!!
        for p in range(len(params_to_iterate)):
            if p == 0:
                config_jnorte["GLACIER"]["DDFG"] = str(params_to_iterate[p])
            elif p == 1:
                config_jnorte["GLACIER"]["DDFDG"] = str(params_to_iterate[p])
            elif p == 2:
                config_jnorte["SNOW"]["TCrit"] = str(params_to_iterate[p])
            elif p == 3:
                config_jnorte["SNOW"]["DDFS"] = str(params_to_iterate[p])
            elif p == 4:
                config_jnorte["ROUTING"]["kx"] = str(params_to_iterate[p])
    
        with open(config_path, 'w') as conf: #Save the config file with the params edited
            config_jnorte.write(conf)
        
        #run sphy
        os.system("python -m SPHY.main -i c:\juncal_norte\TEST_sphy_config_juncal_norte.cfg")
        
        #Read the sim data
        sim_path = r"C:\Users\pauls\Anaconda3\pkgs\sphy-2.2.1-py_0\site-packages\SPHY\Juncal_norte\output\QTOTSubBasinTSS.tss"
        sim_read = pd.read_csv(sim_path,index_col=False,skiprows=4)
        sim = []
        for v in range(len(sim_read)):
            val = sim_read.iloc[v,0].strip()
            val = " ".join(val.split())
            sim.append(val)
        sim = pd.DataFrame(sim)
        sim.columns = ["name"]
        sim = sim["name"].str.split(" ",expand=True)
        sim = pd.DataFrame(sim.iloc[:,2]).astype(float)
        sim = sim.iloc[:,0]
        sim = sim.values

        return sim

class spotpy_setup(object):  
    def __init__(self):
        self.sphymodel = sphy_model() #vic_model(datastart,dataend) # routine to run model

        # model parameters to calibrate #('parameter',min_value,max_value) we have to define these values based on the nc
        #lower bound, upper bound, step size, initial value
        self.params = [spotpy.parameter.Uniform('DDFG',5,15),
                       spotpy.parameter.Uniform('DDFDG',5,15),
                       spotpy.parameter.Uniform('TCrit',-2,8),
                       spotpy.parameter.Uniform('DDFS',1,15),
                       spotpy.parameter.Uniform('kx',0.8,0.99)]

        return
    
    def parameters(self):
        
        return spotpy.parameter.generate(self.params)

    def simulation(self,vector): #OK
        simulations = self.sphymodel.run_sphy(DDFG=vector[0],DDFDG=vector[1],TCrit=vector[2],DDFS=vector[3],kx=vector[4])

        return simulations
    
    def evaluation(self,evaldates=False): #self,evaldates=False
        self.sphymodel.get_obs()
        return self.sphymodel.observations
        
    def objectivefunction(self,simulation,evaluation):

        objectivefunction = -(spotpy.objectivefunctions.nashsutcliffe(evaluation, simulation)-1) #NASH

        return objectivefunction
        
def findBestSim(dbPath):
    csv = pd.read_csv(dbPath+'.csv')

    results = np.array(csv)

    likes = 1-np.abs(np.array(csv.like1))

    idx = likes.argmin() #np.nanargmin 


    i = results[idx,1]
    d = results[idx,2]
    dmax = results[idx,3]
    w = results[idx,4]
    ex = results[idx,5]
    dep = results[idx,6]
    rm = results[idx,7]
    lai = results[idx,8]
    alb = results[idx,9]
    #print("ESTE ES EL RESULTS", dmax)
    
    params = [i,d,dmax,w,ex,dep,rm,lai,alb]
    
    print("ESTE ES EL MEJOR", idx)
    return params

def kge(aa):
    csv_2 = pd.read_csv(aa+'.csv')
    results_2 = np.array(csv_2)
    likes_2 = 1-(np.abs(np.array(csv_2.like1)))
    idx_2 = likes_2.argmin()
    val = results_2[idx_2,0]
    
    return val
    
def runStats(sim,obs):
    nse = 1 - (np.nansum((sim-obs)**2)/np.nansum((obs-obs.mean())**2))
    bias = np.nanmean(sim-obs)
    rmse = np.nanmean(np.sqrt((sim-obs)**2))
    kge = 1-np.sqrt((np.corrcoef(sim,obs)-1)**2+((sim.mean()/obs.mean())-1)**2+(((sim.var()/sim.mean())/(obs.var()/obs.mean()))-1)**2)
    #kge = -(spotpy.objectivefunction.kge(obs,sim)-1) #probar kge

    #print("j")
    return nse, bias, rmse, kge

def calibrate():

    outCal = r"C:\Users\pauls\Desktop\Proyectos\Juncal_norte\Calibration\SCEUA_SPHY" #print("1.2 - outCal")
    # initialize calibration algorithm with
    sampler = spotpy.algorithms.sceua(spotpy_setup(),dbname=outCal,dbformat='csv') #    #print("1 - sampler")
    results = [] # mpty list to append iteration results !!!    #print("2.1 - sampler")
    # run calibration process
    sampler.sample(100) 

    results.append(sampler.getdata()) 

    print("-------------------------------- PSANDOVALQ --------------------------------")
    print("------------------------  https://github.com/SQPaul ------------------------")
    return

    
if __name__ == "__main__":
    calibrate()

