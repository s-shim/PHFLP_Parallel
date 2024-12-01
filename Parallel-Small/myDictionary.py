import pandas as pd
from gurobipy import *
import random
import copy
import math
import datetime
import time

def RR(Y,J,M,theNotSelected,len_r):
    RY = {}
    for j in J:
        for m in M:
            #RY[j,m] = Y[j,m] + (1 - Y[j,m]) * random.random()
            RY[j,m] = Y[j,m] * random.random()
    
    theSelected = []
    notSelected = copy.deepcopy(theNotSelected)
    while len(theSelected) < len_r:
        largest = - 1
        largest_j = -1
        largest_m = -1
        for (j,m) in notSelected:
            if largest < RY[j,m]:
                largest = RY[j,m]
                largest_j = j
                largest_m = m
        theSelected.append((largest_j,largest_m))
        for m in M:
            notSelected.remove((largest_j,m))
    return theSelected



def EvaluatorNL(theSelected,logSum,g,p,I,low,up):
    bestObj = 0.0
    pw = {}
    totalPW = {}
    for i in I:
        totalPW[i] = 0.0
        for (j,m) in theSelected:
            #pw[i,j,m] = (p[i,j,m] / (1 - p[i,j,m])) ** (1 / logSum)
            pw[i,j,m] = pow(p[i,j,m] / (1 - p[i,j,m]), 1 / logSum)
            totalPW[i] += pw[i,j,m]
    
    
    feasibility = True
    
    #### X >= mu_low x Y
    for (j,m) in theSelected:
        LHS = - low[m] 
        for i in I:
            LHS += g[i] * (pw[i,j,m] / totalPW[i]) * pow(totalPW[i], logSum) / (1.0 + pow(totalPW[i], logSum))
        if LHS < 0:
            bestObj = bestObj + LHS
            feasibility = False
            
    
    #### X <= mu_up x Y
    for (j,m) in theSelected:
        if up[m] > 0:
            LHS = - up[m] 
            for i in I:
                LHS += g[i] * (pw[i,j,m] / totalPW[i]) * pow(totalPW[i], logSum) / (1.0 + pow(totalPW[i], logSum))
            if LHS > 0:
                bestObj = bestObj - LHS
                feasibility = False
        
    if feasibility == True:
        objValue = 0.0
        for i in I:
            for (j,m) in theSelected:
                objValue += g[i] * (pw[i,j,m] / totalPW[i]) * math.pow(totalPW[i], logSum) / (1.0 + math.pow(totalPW[i], logSum))
        
        bestObj = objValue
            
    return bestObj, feasibility



def EvaluatorSingle(theSelected,g,p,I,low,up):
    bestObj = 0.0
    pw = {}
    totalPW = {}
    for i in I:
        totalPW[i] = 1.0
        for (j,m) in theSelected:
            pw[i,j,m] = p[i,j,m] / (1 - p[i,j,m])
            totalPW[i] += pw[i,j,m]
    
    
    feasibility = True
    
    #### X >= mu_low x Y
    for (j,m) in theSelected:
        LHS = - low[m] 
        for i in I:
            LHS += g[i] * pw[i,j,m] / totalPW[i]
        if LHS < 0:
            bestObj = bestObj + LHS
            feasibility = False
            
    
    #### X <= mu_up x Y
    for (j,m) in theSelected:
        if up[m] > 0:
            LHS = - up[m] 
            for i in I:
                LHS += g[i] * pw[i,j,m] / totalPW[i]
            if LHS > 0:
                bestObj = bestObj - LHS
                feasibility = False
        
    if feasibility == True:
        objValue = 0.0
        for i in I:
            for (j,m) in theSelected:
                objValue += g[i] * pw[i,j,m] / totalPW[i]
        
        bestObj = objValue
            
    return bestObj, feasibility



def Evaluator(theSelected,g,p,I,low,up):
    bestObj = -1
    pw = {}
    totalPW = {}
    for i in I:
        totalPW[i] = 1.0
        for (j,m) in theSelected:
            pw[i,j,m] = p[i,j,m] / (1 - p[i,j,m])
            totalPW[i] += pw[i,j,m]
    
    
    feasibility = True
    
    #### X >= mu_low x Y
    for (j,m) in theSelected:
        LHS = - low[m] 
        for i in I:
            LHS += g[i] * pw[i,j,m] / totalPW[i]
        if LHS < 0:
            feasibility = False
            break
    
    if feasibility == True:
        #### X <= mu_up x Y
        for (j,m) in theSelected:
            if up[m] > 0:
                LHS = - up[m] 
                for i in I:
                    LHS += g[i] * pw[i,j,m] / totalPW[i]
                if LHS > 0:
                    feasibility = False
                    break                    
        
    if feasibility == True:
        objValue = 0.0
        for i in I:
            for (j,m) in theSelected:
                objValue += g[i] * pw[i,j,m] / totalPW[i]
        
        if bestObj < objValue:
            bestObj = objValue
            
    return bestObj

       


def PHCFLPPRELAX(len_r,g,p,I,J,M,low,up):
    ## ILP Model
    model = Model('PHCFLPP')
    #model.setParam('NumericFocus', 3)
    
    ### employ variables
    x_vars = []
    x_names = []
    for i in I:
        for j in J:
            for m in M:
                x_vars += [(i,j,m)]
                x_names += ['X[%s,%s,%s]'%(i,j,m)]
    X = model.addVars(x_vars, vtype = GRB.CONTINUOUS, name = x_names)
    
    z_vars = []
    z_names = []
    for i in I:
        z_vars += [(i)]
        z_names += ['Z[%s]'%(i)]
    Z = model.addVars(z_vars, vtype = GRB.CONTINUOUS, name = z_names)
    
    y_vars = []
    y_names = []
    for j in J:
        for m in M:
            y_vars += [(j,m)]
            y_names += ['Y[%s,%s]'%(j,m)]
    Y = model.addVars(y_vars, vtype = GRB.BINARY, name = y_names)
    
    ### add constraints
    #### entire probability == 1 for every i
    for i in I:
        LHS = [(1,Z[i])]
        for j in J:
            for m in M:
                LHS += [(1,X[i,j,m])]
        model.addConstr(LinExpr(LHS)==1, name='Eq.entire probability (%s)'%i)
    
    #### X <= Y
    for i in I:
        for j in J:
            for m in M:
                LHS = [(1,X[i,j,m]),(- p[i,j,m],Y[j,m])]
                model.addConstr(LinExpr(LHS)<=0, name='Eq.X <= Y (%s,%s,%s)'%(i,j,m))
    
    #### X <= Z
    for i in I:
        for j in J:
            for m in M:
                LHS = [(1,X[i,j,m]),(- p[i,j,m] / (1 - p[i,j,m]), Z[i])]
                model.addConstr(LinExpr(LHS)<=0, name='Eq.X <= Z (%s,%s,%s)'%(i,j,m))
    
    #### Z <= X
    for i in I:
        for j in J:
            for m in M:
                LHS = [(- (1 - p[i,j,m]) / p[i,j,m], X[i,j,m]), (1, Z[i]), (1, Y[j,m])]
                model.addConstr(LinExpr(LHS)<=1, name='Eq.Z <= X (%s,%s,%s)'%(i,j,m))
    
    #### X >= mu_low x Y
    for j in J:
        for m in M:
            LHS = [(- low[m],Y[j,m])]
            for i in I:
                LHS += [(g[i],X[i,j,m])]
            model.addConstr(LinExpr(LHS)>=0, name='Eq.X >= mu_low x Y (%s,%s)'%(j,m))
    
    #### X <= mu_up x Y
    for j in J:
        for m in M:
            if up[m] > 0:
                LHS = [(- up[m],Y[j,m])]
                for i in I:
                    LHS += [(g[i],X[i,j,m])]
                model.addConstr(LinExpr(LHS)<=0, name='Eq.X <= mu_up x Y (%s,%s)'%(j,m))
    
    #### sum_m Y <= 1
    for j in J:
        LHS = []
        for m in M:
            LHS += [(1,Y[j,m])]
        model.addConstr(LinExpr(LHS)<=1, name='Eq.sum_m Y <= 1 (%s)'%(j))
    
    #### sum Y = len_r
    LHS = []
    for j in J:
        for m in M:
            LHS += [(1,Y[j,m])]
    model.addConstr(LinExpr(LHS)==len_r, name='Eq.sum Y == len_r')
    
    ### set objective
    objTerms = []
    for i in I:
        for j in J:
            for m in M:
                objTerms += [(g[i],X[i,j,m])]
    model.setObjective(LinExpr(objTerms), GRB.MAXIMIZE)
    
    # update and solve the model
    model.update()
    model = model.relax()
    model.optimize()
    
    return model



def PHCFLPP(len_r,g,p,I,J,M,low,up):
    ## ILP Model
    model = Model('PHCFLPP')
    #model.setParam('NumericFocus', 3)
    
    ### employ variables
    x_vars = []
    x_names = []
    for i in I:
        for j in J:
            for m in M:
                x_vars += [(i,j,m)]
                x_names += ['X[%s,%s,%s]'%(i,j,m)]
    X = model.addVars(x_vars, vtype = GRB.CONTINUOUS, name = x_names)
    
    z_vars = []
    z_names = []
    for i in I:
        z_vars += [(i)]
        z_names += ['Z[%s]'%(i)]
    Z = model.addVars(z_vars, vtype = GRB.CONTINUOUS, name = z_names)
    
    y_vars = []
    y_names = []
    for j in J:
        for m in M:
            y_vars += [(j,m)]
            y_names += ['Y[%s,%s]'%(j,m)]
    Y = model.addVars(y_vars, vtype = GRB.BINARY, name = y_names)
    
    ### add constraints
    #### entire probability == 1 for every i
    for i in I:
        LHS = [(1,Z[i])]
        for j in J:
            for m in M:
                LHS += [(1,X[i,j,m])]
        model.addConstr(LinExpr(LHS)==1, name='Eq.entire probability (%s)'%i)
    
    #### X <= Y
    for i in I:
        for j in J:
            for m in M:
                LHS = [(1,X[i,j,m]),(- p[i,j,m],Y[j,m])]
                model.addConstr(LinExpr(LHS)<=0, name='Eq.X <= Y (%s,%s,%s)'%(i,j,m))
    
    #### X <= Z
    for i in I:
        for j in J:
            for m in M:
                LHS = [(1,X[i,j,m]),(- p[i,j,m] / (1 - p[i,j,m]), Z[i])]
                model.addConstr(LinExpr(LHS)<=0, name='Eq.X <= Z (%s,%s,%s)'%(i,j,m))
    
    #### Z <= X
    for i in I:
        for j in J:
            for m in M:
                LHS = [(- (1 - p[i,j,m]) / p[i,j,m], X[i,j,m]), (1, Z[i]), (1, Y[j,m])]
                model.addConstr(LinExpr(LHS)<=1, name='Eq.Z <= X (%s,%s,%s)'%(i,j,m))
    
    #### X >= mu_low x Y
    for j in J:
        for m in M:
            LHS = [(- low[m],Y[j,m])]
            for i in I:
                LHS += [(g[i],X[i,j,m])]
            model.addConstr(LinExpr(LHS)>=0, name='Eq.X >= mu_low x Y (%s,%s)'%(j,m))
    
    #### X <= mu_up x Y
    for j in J:
        for m in M:
            if up[m] > 0:
                LHS = [(- up[m],Y[j,m])]
                for i in I:
                    LHS += [(g[i],X[i,j,m])]
                model.addConstr(LinExpr(LHS)<=0, name='Eq.X <= mu_up x Y (%s,%s)'%(j,m))
    
    #### sum_m Y <= 1
    for j in J:
        LHS = []
        for m in M:
            LHS += [(1,Y[j,m])]
        model.addConstr(LinExpr(LHS)<=1, name='Eq.sum_m Y <= 1 (%s)'%(j))
    
    #### sum Y = len_r
    LHS = []
    for j in J:
        for m in M:
            LHS += [(1,Y[j,m])]
    model.addConstr(LinExpr(LHS)==len_r, name='Eq.sum Y == len_r')
    
    ### set objective
    objTerms = []
    for i in I:
        for j in J:
            for m in M:
                objTerms += [(g[i],X[i,j,m])]
    model.setObjective(LinExpr(objTerms), GRB.MAXIMIZE)
    
    # update and solve the model
    model.update()
    model.optimize()
    
    return model



def PHCFLPPJFIX(g,p,I,J,M,low,up):
    ## ILP Model
    model = Model('PHCFLPP')
    #model.setParam('NumericFocus', 3)
    
    ### employ variables
    x_vars = []
    x_names = []
    for i in I:
        for j in J:
            for m in M:
                x_vars += [(i,j,m)]
                x_names += ['X[%s,%s,%s]'%(i,j,m)]
    X = model.addVars(x_vars, vtype = GRB.CONTINUOUS, name = x_names)
    
    z_vars = []
    z_names = []
    for i in I:
        z_vars += [(i)]
        z_names += ['Z[%s]'%(i)]
    Z = model.addVars(z_vars, vtype = GRB.CONTINUOUS, name = z_names)
    
    y_vars = []
    y_names = []
    for j in J:
        for m in M:
            y_vars += [(j,m)]
            y_names += ['Y[%s,%s]'%(j,m)]
    Y = model.addVars(y_vars, vtype = GRB.BINARY, name = y_names)
    
    ### add constraints
    #### entire probability == 1 for every i
    for i in I:
        LHS = [(1,Z[i])]
        for j in J:
            for m in M:
                LHS += [(1,X[i,j,m])]
        model.addConstr(LinExpr(LHS)==1, name='Eq.entire probability (%s)'%i)
    
    #### X <= Y
    for i in I:
        for j in J:
            for m in M:
                LHS = [(1,X[i,j,m]),(- p[i,j,m],Y[j,m])]
                model.addConstr(LinExpr(LHS)<=0, name='Eq.X <= Y (%s,%s,%s)'%(i,j,m))
    
    #### X <= Z
    for i in I:
        for j in J:
            for m in M:
                LHS = [(1,X[i,j,m]),(- p[i,j,m] / (1 - p[i,j,m]), Z[i])]
                model.addConstr(LinExpr(LHS)<=0, name='Eq.X <= Z (%s,%s,%s)'%(i,j,m))
    
    #### Z <= X
    for i in I:
        for j in J:
            for m in M:
                LHS = [(- (1 - p[i,j,m]) / p[i,j,m], X[i,j,m]), (1, Z[i]), (1, Y[j,m])]
                model.addConstr(LinExpr(LHS)<=1, name='Eq.Z <= X (%s,%s,%s)'%(i,j,m))
    
    #### X >= mu_low x Y
    for j in J:
        for m in M:
            LHS = [(- low[m],Y[j,m])]
            for i in I:
                LHS += [(g[i],X[i,j,m])]
            model.addConstr(LinExpr(LHS)>=0, name='Eq.X >= mu_low x Y (%s,%s)'%(j,m))
    
    #### X <= mu_up x Y
    for j in J:
        for m in M:
            if up[m] > 0:
                LHS = [(- up[m],Y[j,m])]
                for i in I:
                    LHS += [(g[i],X[i,j,m])]
                model.addConstr(LinExpr(LHS)<=0, name='Eq.X <= mu_up x Y (%s,%s)'%(j,m))
    
    #### sum_m Y == 1
    for j in J:
        LHS = []
        for m in M:
            LHS += [(1,Y[j,m])]
        model.addConstr(LinExpr(LHS)==1, name='Eq.sum_m Y == 1 (%s)'%(j))
        
    ### set objective
    objTerms = []
    for i in I:
        for j in J:
            for m in M:
                objTerms += [(g[i],X[i,j,m])]
    model.setObjective(LinExpr(objTerms), GRB.MAXIMIZE)
    
    # update and solve the model
    model.update()
    model.optimize()
    
    return model




def parallelRR(iteration,Centroid,J,M,theNotSelected,len_r,logSum,g,p,I,low,up,fileName,instance,timeLimit,machineName):
    Y = copy.deepcopy(Centroid)
    bestSelected = RR(Y,J,M,theNotSelected,len_r)
    #bestSelected = sorted(bestSelected)
    bestObj, feasibility = EvaluatorNL(bestSelected,logSum,g,p,I,low,up)
    print(bestObj, feasibility, bestSelected)
    print()
    print()
    print(datetime.datetime.now())
    tic = time.time()
    nLocal = 0
    
    # =============================================================================
    # print('####### Start %s trials of Randomized Rounding #######'%trials)
    # for trial in range(trials):
    # =============================================================================
    print('###### File %s'%fileName)            
    print('####### Instance %s #######'%instance)    
    print('####### Iteration %s #######'%iteration)    
    print('####### Start Randomized Rounding for %s seconds #######'%timeLimit)    
    trial = 0
    toc = time.time()

    machineArray = [machineName]
    fileArray = [fileName]
    instanceArray = [instance]
    iterationArray = [iteration]
    bestTrial = trial
    trialArray = [bestTrial]
    bestTime = toc - tic
    timeArray = [bestTime]
    objectiveArray = [bestObj]
    logSumArray = [logSum]
    intY = {}
    for j in J:
        for m in M:
            if (j,m) in bestSelected:
                intY[j,m] = [1]
            else:
                intY[j,m] = [0]

    summaryTable = pd.DataFrame(list(zip(machineArray,fileArray,instanceArray,logSumArray,iterationArray,trialArray,timeArray,objectiveArray)),columns =['Machine','File Name','Instance','logSum','Iteration','Trial','Time','Objective'])
    for j in J:
        for m in M:
            summaryTable['Y[%s,%s]'%(j,m)] = intY[j,m]
            
    summaryTable.to_csv(r'Parallel_%s_Instance%s_logSum%s_Core%s.csv'%(fileName,instance,int(logSum * 100),iteration), index = False)#Check

    while toc - tic < timeLimit:
        trial += 1
        #print(trial)
        
        theSelected = RR(Y,J,M,theNotSelected,len_r)
        #theSelected = sorted(theSelected)
        same = True
        for (j,m) in theSelected:
            if (j,m) not in bestSelected:
                same = False
                break
    
        RMSD = 0.0
        for j in J:
            for m in M:
                RMSD = RMSD + (Y[j,m] - Centroid[j,m]) ** 2
        RMSD = RMSD / (len(J) * len(M))
        RMSD = math.sqrt(RMSD)
        
        #print(trial,RMSD)
        
        reset = False            
        if same == True:
            nLocal += 1
            if random.random() < min(1, nLocal / 20) * RMSD:
                reset = True
                nLocal = 0
        else:
            nLocal = 0
            objective, feasibility = EvaluatorNL(theSelected,logSum,g,p,I,low,up)
            if bestObj < objective:
                bestObj = objective
                bestSelected = copy.deepcopy(theSelected)
                print()
                print('trial=',trial)            
                print('bestObj=',bestObj)
                print('logSum=',logSum)
                toc = time.time()
                print('time=',toc - tic)
                
                machineArray += [machineName]
                fileArray += [fileName]
                instanceArray += [instance]
                iterationArray += [iteration]
                bestTrial = trial
                trialArray += [bestTrial]
                bestTime = toc - tic
                timeArray += [bestTime]
                objectiveArray += [bestObj]
                logSumArray += [logSum]
                
                for j in J:
                    for m in M:
                        if (j,m) in bestSelected:
                            intY[j,m] += [1]
                        else:
                            intY[j,m] += [0]
            
                summaryTable = pd.DataFrame(list(zip(machineArray,fileArray,instanceArray,logSumArray,iterationArray,trialArray,timeArray,objectiveArray)),columns =['Machine','File Name','Instance','logSum','Iteration','Trial','Time','Objective'])
                for j in J:
                    for m in M:
                        summaryTable['Y[%s,%s]'%(j,m)] = intY[j,m]
                        
                summaryTable.to_csv(r'Parallel_%s_Instance%s_logSum%s_Core%s.csv'%(fileName,instance,int(logSum * 100),iteration), index = False)#Check
    
        if reset == True:
            Y = copy.deepcopy(Centroid)
        else:
            alpha = 1 / (1 + math.exp(4 * RMSD))
            for j in J:
                for m in M:
                    Y[j,m] = (1 - alpha) * Y[j,m]
                    if (j,m) in bestSelected:
                        Y[j,m] = Y[j,m] + alpha
    
        toc = time.time()
    
    print()
    print('%s trials DONE'%trial)    
    print('Instance =',instance)
    print('Iteration =',iteration)
    print('time =',toc-tic)                    
    
    machineArray += ['END']
    fileArray += [fileName]
    instanceArray += [instance]
    iterationArray += [iteration]
    trialArray += [trial]
    timeArray += [toc-tic]
    objectiveArray += [bestObj]
    logSumArray += [logSum]
    
    for j in J:
        for m in M:
            if (j,m) in bestSelected:
                intY[j,m] += [1]
            else:
                intY[j,m] += [0]

    summaryTable = pd.DataFrame(list(zip(machineArray,fileArray,instanceArray,logSumArray,iterationArray,trialArray,timeArray,objectiveArray)),columns =['Machine','File Name','Instance','logSum','Iteration','Trial','Time','Objective'])
    for j in J:
        for m in M:
            summaryTable['Y[%s,%s]'%(j,m)] = intY[j,m]
            
    summaryTable.to_csv(r'Parallel_%s_Instance%s_logSum%s_Core%s.csv'%(fileName,instance,int(logSum * 100),iteration), index = False)#Check
    
    return bestObj, bestTime, bestTrial, iteration
            
            
            

def parallelRR2(args):

    iteration,Centroid,J,M,theNotSelected,len_r,logSum,g,p,I,low,up,fileName,instance,timeLimit,machineName = args

    return parallelRR(iteration,Centroid,J,M,theNotSelected,len_r,logSum,g,p,I,low,up,fileName,instance,timeLimit,machineName)            
            
        





