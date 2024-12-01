import socket
import pandas as pd
from gurobipy import *
import copy
import datetime
import time
import random
from itertools import product
import myDictionary as md
import math
import multiprocessing as mp

machineName = socket.gethostname()
logSum = 0.5

# =============================================================================
# fileName = 'M6_J15_I400_r8'
# fileName1 = 'M6_J15_I400_r8 - Part 1 of 3'
# fileName2 = 'M6_J15_I400_r8 - Part 2 of 3'
# fileName3 = 'M6_J15_I400_r8 - Part 3 of 3'
# =============================================================================

# =============================================================================
# fileName = 'M6_J10_I400_r5'
# fileName1 = 'M6_J10_I400_r5 - Part 1 of 2'
# fileName2 = 'M6_J10_I400_r5 - Part 1 of 2'
# fileName3 = 'M6_J10_I400_r5 - Part 2 of 2'
# =============================================================================

fileName = 'M4_J15_I400_r8'
fileName1 = 'M4_J15_I400_r8 - Part 1 of 2'
fileName2 = 'M4_J15_I400_r8 - Part 1 of 2'
fileName3 = 'M4_J15_I400_r8 - Part 2 of 2'

# =============================================================================
# for fileName in ['M4_J05_I050_r3','M4_J10_I050_r5','M4_J15_I050_r8','M6_J05_I050_r3','M6_J10_I050_r5','M6_J15_I050_r8','M4_J05_I100_r3','M4_J10_I100_r5','M4_J15_I100_r8','M6_J05_I100_r3','M6_J10_I100_r5','M6_J15_I100_r8','M4_J05_I200_r3','M4_J10_I200_r5','M4_J15_I200_r8','M6_J05_I200_r3','M6_J10_I200_r5','M6_J15_I200_r8','M4_J05_I400_r3','M4_J10_I400_r5','M6_J05_I400_r3','M6_J10_I400_r5']:
#     fileName1 = fileName # 'M6_J15_I400_r8 - Part 1 of 3'
#     fileName2 = fileName # 'M6_J15_I400_r8 - Part 2 of 3'
#     fileName3 = fileName # 'M6_J15_I400_r8 - Part 3 of 3'
# =============================================================================

#iterations = 1
# trials = 10000
timeLimit = 60 * 60 * 1 # seconds

print()
print('###### Randomized Rounding %s'%fileName,datetime.datetime.now())


filePath = '../data_Urwolfen/%s.xlsx'%fileName
filePath1 = '../data_Urwolfen/%s.xlsx'%fileName1
filePath2 = '../data_Urwolfen/%s.xlsx'%fileName2
filePath3 = '../data_Urwolfen/%s.xlsx'%fileName3

g_all = pd.read_excel(open(filePath1, 'rb'), sheet_name='g_all', header = 2)
p_all = pd.read_excel(open(filePath2, 'rb'), sheet_name='p_all', header = 2)
I = pd.read_excel(open(filePath1, 'rb'), sheet_name='I', header = 1)
I = I.drop([0])
I = list(I['I'])
J = pd.read_excel(open(filePath1, 'rb'), sheet_name='J', header = 1)
J = J.drop([0])
J = list(J['J'])
M = pd.read_excel(open(filePath1, 'rb'), sheet_name='M', header = 1)
M = M.drop([0])
M = list(M['M'])
mu = pd.read_excel(open(filePath1, 'rb'), sheet_name='mu', header = 2)
Scalar = pd.read_excel(open(filePath1, 'rb'), sheet_name='Scalar', header = 1)
[len_r] = Scalar.loc[Scalar['Parameter']=='r','Value']


machineArray = []
fileArray = []
instanceArray = []
coreArray = []
iterationArray = []
timeArray = []
objectiveArray = []
logSumArray = []

for instance in range(1,10+1):   
    print()     
    print('####### Instance =',instance,datetime.datetime.now())
    ## extract instance
    ## extract instance
    g_instance = g_all.loc[g_all['instance']=='inst%s'%instance]
    g = {}
    for i in I:
        [g[i]] = g_instance.loc[g_instance['I']==i,'Value']
    
    p = {}
    p_instance = p_all.loc[p_all['instance']=='inst%s'%instance]
    for i in I:
        for j in J:
            for m in M:
                [p[i,j,m]] = p_instance.loc[(p_instance['I']==i)&(p_instance['J']==j)&(p_instance['Modes']==m),'Value']
    
    mode_names = []
    mode_low = []
    mode_up = []
    for m in M:
        mode_names += [m]
        if m not in list(mu['Modes']):
            mode_low += [0]
        else:
            [low] = mu.loc[mu['Modes']==m,'Value']
            mode_low += [low]
            mode_up += [low]
    mode_up += [-1]
    modeTable = pd.DataFrame(list(zip(mode_names,mode_low,mode_up)),columns =['Modes','Lower Bound','Upper Bound'])
    
    low = {}
    up = {}
    for m in M:
        [m_low] = modeTable.loc[modeTable['Modes']==m,'Lower Bound']
        [m_up] = modeTable.loc[modeTable['Modes']==m,'Upper Bound']
        low[m] = m_low
        up[m] = m_up
    
    
    # =============================================================================
    # model = md.PHCFLPPRELAX(len_r,g,p,I,J,M,low,up)
    # variableName = []
    # variableValue = []
    # for v in model.getVars():
    #     if v.varname[0] == 'Y':
    #         variableName += [v.varname]
    #         variableValue += [v.x]
    #         print(v.varname,'=',v.x)
    # relaxSolution = pd.DataFrame(list(zip(variableName, variableValue)),columns =['varName', 'varVal'])
    # =============================================================================
                
    Centroid = {}
    Zero = {}
    theNotSelected = []
    for j in J:
        for m in M:
            Centroid[j,m] = 0.5
            Zero[j,m] = 0.0
            theNotSelected += [(j,m)]
        
    if __name__ == '__main__':

        numCores = mp.cpu_count()
        parallel = mp.Pool(numCores)

        multiArgs = []  
        for coreID in range(numCores):
            multiArgs += [(coreID,Centroid,J,M,theNotSelected,len_r,logSum,g,p,I,low,up,fileName,instance,timeLimit,machineName)]  

        results = parallel.map(md.parallelRR2, multiArgs)

        maxObj = -1
        minTime = timeLimit
        bestIteration = -1
        for bestObj, bestTime, bestTrial, iteration in results:

            print(bestObj, bestTime, bestTrial, iteration)
            
            if maxObj < bestObj + 10 ** (-9) and maxObj > bestObj - 10 ** (-9):
                if minTime > bestTime:
                    minTime = bestTime
                    bestIteration = iteration
                    
            if maxObj < bestObj - 10 ** (-9):
                maxObj = bestObj
                minTime = bestTime
                bestIteration = iteration
                
        machineArray += [machineName]
        fileArray += [fileName]
        instanceArray += [instance]
        coreArray += [numCores]
        iterationArray += [bestIteration]
        timeArray += [minTime]
        objectiveArray += [maxObj]
        logSumArray += [logSum]
    
        summaryTable = pd.DataFrame(list(zip(machineArray,fileArray,instanceArray,logSumArray,coreArray,iterationArray,timeArray,objectiveArray)),columns =['Machine','File Name','Instance','logSum','Cores','Iteration','Time','Objective'])                   
        summaryTable.to_csv(r'Summary_%s_logSum%s.csv'%(fileName,int(logSum * 100)), index = False)#Check

                
            
