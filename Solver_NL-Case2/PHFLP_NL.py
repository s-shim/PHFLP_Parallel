import socket
import pandas as pd
from gurobipy import *
import copy
import datetime
import time
import random
from itertools import product
import myDictionary as md
import myDictionary_GUROBI as mdg
import math

machineName = socket.gethostname()
print(datetime.datetime.now())

logSum = 0.5
instance = 0
tic = time.time()
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

# threshold of M 
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

pw = {}
for i in I:
    for j in J:
        for m in M:
            pw[i,j,m] = pow(p[i,j,m] / (1 - p[i,j,m]), 1 / logSum)

toc = time.time()
print('time to read data =',toc-tic)
print(datetime.datetime.now())

grand = pd.read_csv('GrandSummary_%s_logSum%s.csv'%(fileName,int(logSum*100))) # 

machineNameArray = []
fileNameArray = []    
instanceArray = []
objArray = []
runTimeArray = []
xobjArray = []

print()
print('###### GUROBI Solves File %s'%fileName,datetime.datetime.now())
print('####### Instance =',instance,datetime.datetime.now())

## extract instance
g_instance = g_all.loc[g_all['instance']=='inst%s'%instance]
g = {}
for i in I:
    [g[i]] = g_instance.loc[g_instance['I']==i,'Value']

p = {}
pw = {}
p_instance = p_all.loc[p_all['instance']=='inst%s'%instance]
for i in I:
    for j in J:
        for m in M:
            [p[i,j,m]] = p_instance.loc[(p_instance['I']==i)&(p_instance['J']==j)&(p_instance['Modes']==m),'Value']
            pw[i,j,m] = pow(p[i,j,m] / (1 - p[i,j,m]), 1 / logSum)

   
print()
print('##### GUROBI Solves File%s Instance%s'%(fileName,instance))

## ILP Model
model = Model('PHFLP')
model.setParam('LogFile','Log_%s_%s_Instance%s_logSum%s.txt'%(machineName,fileName,instance,int(logSum * 100))) 
model, PJM, Y = mdg.PHFLP_NL(model,logSum,len_r,g,p,pw,I,J,M,low,up)


def mycallback(model, where):
    if where == GRB.Callback.MIPSOL:
        # make a list of edges selected in the solution
        pjmVal = {}
        yVal = {}

        SUM = {}
        sumV = {}
        for i in I:
            SUM[i] = []
            sumV[i] = 0.0
            for j in J:
                for m in M:
                    pjmVal[i,j,m] = model.cbGetSolution(PJM[i,j,m])
                    SUM[i] += [(1,PJM[i,j,m])]
                    sumV[i] += pjmVal[i,j,m]

        for j in J:
            for m in M:
                yVal[j,m] = model.cbGetSolution(Y[j,m])
            
        z_iYINT = {}
        wHat = {}
        wHatPrime = {}
        for i in I:
            z_iYINT[i] = 0.0
            for j in J:
                for m in M:
                    z_iYINT[i] += pw[i,j,m] * yVal[j,m]                            
            wHat[i] = pow(z_iYINT[i],logSum) / (1 + pow(z_iYINT[i],logSum))
            wHatPrime[i] = logSum * pow(z_iYINT[i],logSum - 1) / pow(1 + pow(z_iYINT[i],logSum),2)
                    
        for i in I:
            if sumV[i] > wHat[i] + pow(10,-9):
                LHS = SUM[i] + []
                rhs = wHat[i] 
                for j in J:
                    for m in M:
                        LHS += [(- wHatPrime[i] * pw[i,j,m], Y[j,m])]
                        rhs = rhs - wHatPrime[i] * pw[i,j,m] * yVal[j,m]                            
                model.cbLazy(LinExpr(LHS)<=rhs)

            if sumV[i] < wHat[i] - pow(10,-9):
                LHS = SUM[i] + []
                rhs = wHat[i] 
                for j in J:
                    for m in M:
                        if yVal[j,m] > 1 - pow(10,-9):
                            LHS += [(-1,Y[j,m])]
                            rhs = rhs - 1
                        if yVal[j,m] < 0 + pow(10,-9):
                            LHS += [(+1,Y[j,m])]
                model.cbLazy(LinExpr(LHS)>=rhs)


# Warm Start
grandSelected = []
for j in J:
    for m in M:
        [yVal] = grand.loc[grand['Instance']==instance,'Y[%s,%s]'%(j,m)]
        if yVal == 1:
            Y[j,m].start = 1                
            grandSelected += [(j,m)]
        if yVal == 0:
            Y[j,m].start = 0                

grandValue, grandFeasibility, grandChoiceP = md.EvaluatorNL2(grandSelected,logSum,g,p,I,J,M,low,up) 
for i in I:
    for j in J:
        for m in M:
            PJM[i,j,m].start = grandChoiceP[i,j,m]


# update and solve the model
model.update()
model.Params.lazyConstraints = 1
model.optimize(mycallback)

# read the optimal solution
variableName = []
variableValue = []
for v in model.getVars():
    variableName += [v.varname]
    variableValue += [v.x]

optSolution = pd.DataFrame(list(zip(variableName, variableValue)),columns =['varName', 'varVal'])
# optSolution.to_csv(r'optSol_%s_Instance%s_logSum%s.txt'%(fileName,instance,int(logSum * 100)), index = False)#Check #


# evaluate optimal solution
YY = {}
theSelected = []
for j in J:
    for m in M:
        [varVal] = optSolution.loc[optSolution['varName']=='Y[%s,%s]'%(j,m),'varVal']
        if varVal > 1 - pow(10,-9):
            YY[j,m] = 1.0
            theSelected += [(j,m)]
        else:
            YY[j,m] = 0.0
            
objValue, feasibility, choiceP = md.EvaluatorNL2(theSelected,logSum,g,p,I,J,M,low,up) 

print('Evaluate optSolution=',objValue)

machineNameArray += [machineName]
fileNameArray += [fileName]    
instanceArray += [instance]
objArray += [model.ObjVal]
runTimeArray += [model.Runtime]
xobjArray += [objValue]

optValue = pd.DataFrame(list(zip(fileNameArray,instanceArray, objArray,xobjArray,runTimeArray,machineNameArray)),columns =['fileName','instance','optValue','xOptValue','System Time','Machine'])
optValue.to_csv(r'summaryMILP_%s_logSum%s.csv'%(fileName,int(logSum * 100)), index = False)#Check 




    