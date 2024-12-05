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
logSum = 0.5

# =============================================================================
# fileName = 'M6_J15_I400_r8'
# fileName1 = 'M6_J15_I400_r8 - Part 1 of 3'
# fileName2 = 'M6_J15_I400_r8 - Part 2 of 3'
# fileName3 = 'M6_J15_I400_r8 - Part 3 of 3'
# =============================================================================

fileName = 'M6_J10_I400_r5'
fileName1 = 'M6_J10_I400_r5 - Part 1 of 2'
fileName2 = 'M6_J10_I400_r5 - Part 1 of 2'
fileName3 = 'M6_J10_I400_r5 - Part 2 of 2'

# =============================================================================
# fileName = 'M4_J15_I400_r8'
# fileName1 = 'M4_J15_I400_r8 - Part 1 of 2'
# fileName2 = 'M4_J15_I400_r8 - Part 1 of 2'
# fileName3 = 'M4_J15_I400_r8 - Part 2 of 2'
# =============================================================================

# =============================================================================
# fileName = 'M4_J05_I050_r3'
# for fileName in ['M4_J05_I050_r3','M4_J10_I050_r5','M4_J15_I050_r8','M6_J05_I050_r3','M6_J10_I050_r5','M6_J15_I050_r8','M4_J05_I100_r3','M4_J10_I100_r5','M4_J15_I100_r8','M6_J05_I100_r3','M6_J10_I100_r5','M6_J15_I100_r8','M4_J05_I200_r3','M4_J10_I200_r5','M4_J15_I200_r8','M6_J05_I200_r3','M6_J10_I200_r5','M6_J15_I200_r8','M4_J05_I400_r3','M4_J10_I400_r5','M6_J05_I400_r3']:        
#     fileName1 = fileName # 'M6_J15_I400_r8 - Part 1 of 3'
#     fileName2 = fileName # 'M6_J15_I400_r8 - Part 2 of 3'
#     fileName3 = fileName # 'M6_J15_I400_r8 - Part 3 of 3'
# =============================================================================
        
print()
print('###### GUROBI Solves File %s'%fileName,datetime.datetime.now())

filePath = '../data_Urwolfen/%s.xlsx'%fileName
filePath1 = '../data_Urwolfen/%s.xlsx'%fileName1
filePath2 = '../data_Urwolfen/%s.xlsx'%fileName2
filePath3 = '../data_Urwolfen/%s.xlsx'%fileName3

Y_all = pd.read_excel(open(filePath3, 'rb'), sheet_name='Y_all', header = 2)
F_all = pd.read_excel(open(filePath1, 'rb'), sheet_name='F_all', header = 2)
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

grand = pd.read_csv('GrandSummary_%s_logSum%s.csv'%(fileName,int(logSum*100))) # 

machineNameArray = []
fileNameArray = []    
instanceArray = []
objArray = []
runTimeArray = []
xobjArray = []
for instance in range(1,10+1):   
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
    
    
    
    
        