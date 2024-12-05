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

instance = 0
timeLimit = 3600 * 2

tic = time.time()
#fileName = 'M4_J05_I050_r3_inst1'
fileName = 'Case Study Sydney'

filePath_g = '../data_Urwolfen/%s - g.xlsx'%fileName
filePath_p = '../data_Urwolfen/%s - p.xlsx'%fileName
filePath_Y = '../data_Urwolfen/%s - Y.xlsx'%fileName

g_all = pd.read_excel(open(filePath_g, 'rb'), sheet_name='Tabelle2', header = None)
p_all = pd.read_excel(open(filePath_p, 'rb'), sheet_name='Tabelle2', header = None)
Y_all = pd.read_excel(open(filePath_Y, 'rb'), sheet_name='Tabelle2', header = 0)

Y_all.rename( columns={'Unnamed: 0':'J'}, inplace=True )
Y_all.rename( columns={'Unnamed: 1':'M'}, inplace=True )

M = list(Y_all['M'])
M = set(M)
M = list(M)
M.sort()
print('M =',M)
I = list(g_all[0])
print('len(I) =',len(I))
J = list(Y_all['J'])
J = set(J)
J = list(J)
J.sort()
print('len(J) =',len(J))


low = {}
up = {}
low['1w'] = 0
low['4w'] = 10000
up['1w'] = 10000     
up['4w'] = -1     
print('low_M =',low)
print('up_M =',up)

g = {}
for i in I:
    [g[i]] = g_all.loc[g_all[0]==i,1]

Y_selected = Y_all.loc[Y_all['Level']==1]    
len_r = len(Y_selected)
print('r =',len_r)

toc = time.time()
print('time to read data before reading p =',toc-tic)
print(datetime.datetime.now())

p = {}
for i in I:
    for j in J:
        for m in M:
            p[i,j,m] = 0.0
            
p_all = p_all.reset_index()  # make sure indexes pair with number of rows
for index, row in p_all.iterrows():
    i = row[0]
    j = row[1]
    m = row[2]
    value_ijm = row[3]
    p[i,j,m] += value_ijm

toc = time.time()
print('time to read data =',toc-tic)
print(datetime.datetime.now())

            
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
            
    machineArray = [machineName]
    fileArray = [fileName]
    instanceArray = [instance]
    coreArray = [numCores]
    iterationArray = [bestIteration]
    timeArray = [minTime]
    objectiveArray = [maxObj]
    logSumArray = [logSum]

    summaryTable = pd.DataFrame(list(zip(machineArray,fileArray,instanceArray,logSumArray,coreArray,iterationArray,timeArray,objectiveArray)),columns =['Machine','File Name','Instance','logSum','Cores','Iteration','Time','Objective'])                   
    summaryTable.to_csv(r'Summary_%s_logSum%s.csv'%(fileName,int(logSum * 100)), index = False)#Check

            
        
