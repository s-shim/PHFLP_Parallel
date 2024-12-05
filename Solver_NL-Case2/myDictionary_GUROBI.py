import pandas as pd
from gurobipy import *
import random
import copy
import math


def PHFLPNL2(model,logSum,len_r,g,p,pw,I,J,M,low,up): # PHFLP_NL(model,logSum,len_r,g,p,I,J,M,low,up)
    ### employ variables
    pjm_vars = []
    pjm_names = []
    for i in I:
        for j in J:
            for m in M:
                pjm_vars += [(i,j,m)]
                pjm_names += ['PJM[%s,%s,%s]'%(i,j,m)]
    PJM = model.addVars(pjm_vars, vtype = GRB.CONTINUOUS, name = pjm_names)
    
    # =============================================================================
    # pno_vars = []
    # pno_names = []
    # for i in I:
    #     pno_vars += [(i)]
    #     pno_names += ['PNO[%s]'%(i)]
    # PNO = model.addVars(pno_vars, vtype = GRB.CONTINUOUS, name = pno_names)
    # =============================================================================
    
    y_vars = []
    y_names = []
    for j in J:
        for m in M:
            y_vars += [(j,m)]
            y_names += ['Y[%s,%s]'%(j,m)]
    Y = model.addVars(y_vars, vtype = GRB.BINARY, name = y_names)
    
    ### add constraints
    # =============================================================================
    # #### entire probability == 1 for every i : strengthen the model
    # for i in I:
    #     LHS = [(1,PNO[i])]
    #     for j in J:
    #         for m in M:
    #             LHS += [(1,PJM[i,j,m])]
    #     model.addConstr(LinExpr(LHS)==1, name='Eq.entire probability (%s)'%i)
    # =============================================================================
    
    #### X <= Y : strengthen the model (required?)
    for i in I:
        for j in J:
            for m in M:
                LHS = [(1,PJM[i,j,m]),(- 1,Y[j,m])]
                model.addConstr(LinExpr(LHS)<=0, name='Eq.X <= Y (%s,%s,%s)'%(i,j,m))
    
    #### X <= X : Required
    for i in I:
        for j in J:
            for m in M:
                for k in J:
                    for n in M:
                        if j != k or m != n:
                            if pw[i,k,n] > pow(10,-9):
                                LHS = [(1,PJM[i,j,m]),(- pw[i,j,m] / pw[i,k,n], PJM[i,k,n]),(1,Y[k,n])]
                                model.addConstr(LinExpr(LHS)<=1, name='Eq.X <= Z (%s,%s,%s,%s,%s)'%(i,j,m,k,n))
    
    
    #### X >= mu_low x Y : Done
    for j in J:
        for m in M:
            LHS = [(- low[m],Y[j,m])]
            for i in I:
                LHS += [(g[i],PJM[i,j,m])]
            model.addConstr(LinExpr(LHS)>=0, name='Eq.X >= mu_low x Y (%s,%s)'%(j,m))
    
    #### X <= mu_up x Y : Done
    for j in J:
        for m in M:
            if up[m] > 0:
                LHS = [(- up[m],Y[j,m])]
                for i in I:
                    LHS += [(g[i],PJM[i,j,m])]
                model.addConstr(LinExpr(LHS)<=0, name='Eq.X <= mu_up x Y (%s,%s)'%(j,m))
    
    #### sum_m Y <= 1 : Done
    for j in J:
        LHS = []
        for m in M:
            LHS += [(1,Y[j,m])]
        model.addConstr(LinExpr(LHS)<=1, name='Eq.sum_m Y <= 1 (%s)'%(j))
    
    #### sum Y = len_r : Done
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
                objTerms += [(g[i],PJM[i,j,m])]
    model.setObjective(LinExpr(objTerms), GRB.MAXIMIZE)
        
    return model, PJM, Y



def PHCFLPPStrong(model,len_r,g,p,ub_p,z_ub,z_lb,I,J,M,low,up):
    
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
                LHS = [(1,X[i,j,m]),(- ub_p[i,j,m],Y[j,m])]
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
    
    #### Z < z_ub and Z > z_lb
    for i in I:
        LHS = [(1,Z[i])]
        model.addConstr(LinExpr(LHS)<=z_ub[i], name='Eq.Z<z_ub(%s)'%i)
        model.addConstr(LinExpr(LHS)>=z_lb[i], name='Eq.Z>z_lb(%s)'%i)
    
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



def PHFLPMNL(model,len_r,g,p,I,J,M,low,up): # PHFLP_NL(model,logSum,len_r,g,p,I,J,M,low,up)
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
