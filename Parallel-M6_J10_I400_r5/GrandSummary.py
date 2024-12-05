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
# for fileName in ['M4_J05_I050_r3','M4_J10_I050_r5','M4_J15_I050_r8','M6_J05_I050_r3','M6_J10_I050_r5','M6_J15_I050_r8','M4_J05_I100_r3','M4_J10_I100_r5','M4_J15_I100_r8','M6_J05_I100_r3','M6_J10_I100_r5','M6_J15_I100_r8','M4_J05_I200_r3','M4_J10_I200_r5','M4_J15_I200_r8','M6_J05_I200_r3','M6_J10_I200_r5','M6_J15_I200_r8','M4_J05_I400_r3','M4_J10_I400_r5','M6_J05_I400_r3']:
#     fileName1 = fileName # 'M6_J15_I400_r8 - Part 1 of 3'
#     fileName2 = fileName # 'M6_J15_I400_r8 - Part 2 of 3'
#     fileName3 = fileName # 'M6_J15_I400_r8 - Part 3 of 3'    
# =============================================================================
    
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

        


















