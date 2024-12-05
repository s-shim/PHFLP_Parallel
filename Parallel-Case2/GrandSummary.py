import socket
import pandas as pd
#from gurobipy import *
import copy
import datetime
import time
import random
from itertools import product
import myDictionary as md
import math
#import multiprocessing as mp

machineName = socket.gethostname()
logSum = 0.5

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


summary = pd.read_csv('Summary_%s_logSum%s.csv'%(fileName,int(logSum * 100)))
yInst = {}
for inst in summary['Instance']:
    [iteration] = summary.loc[summary['Instance']==inst,'Iteration']
    # Parallel_M6_J15_I200_r8_Instance10_logSum50_Core127.csv
    parallel = pd.read_csv('Parallel_%s_Instance%s_logSum%s_Core%s.csv'%(fileName,inst,int(logSum * 100),iteration))
    for j in J:
        for m in M:
            [yInst[inst,j,m]] = parallel.loc[parallel['Machine']=='END','Y[%s,%s]'%(j,m)]
        

for j in J:
    for m in M:
        yColumn = []
        for inst in summary['Instance']:
            yColumn += [yInst[inst,j,m]]
        summary['Y[%s,%s]'%(j,m)] = yColumn
        
summary.to_csv(r'GrandSummary_%s_logSum%s.csv'%(fileName,int(logSum * 100)), index = False)#Check

        


















