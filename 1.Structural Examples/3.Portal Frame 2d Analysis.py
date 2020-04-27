from openseespy.opensees import *
from openseespy.postprocessing.Get_Rendering import * 
from math import asin, sqrt
# two dimensional frame: eigenvalue & static load

wipe()

model('Basic','-ndm',2)

# properties
numBay = 2
numFloor = 7

bayWidth = 360.0
storyHeights = [162.0, 162.0, 156.0, 156.0, 156.0, 156.0, 156.0]

E = 29500.0
massX = 0.49
M = 0.
coordTransf = 'Linear'
massType = '-lmass'

beams = ['W24X160', 'W24X160', 'W24X130', 'W24X130', 'W24X110', 'W24X110', 'W24X110']
eColumn = ['W14X246', 'W14X246', 'W14X246', 'W14X211', 'W14X211', 'W14X176', 'W14X176']
iColumn = ['W14X287', 'W14X287', 'W14X287', 'W14X246', 'W14X246', 'W14X211', 'W14X211']
columns = [eColumn, iColumn, eColumn]

# properties of the section
WSection = {
    'W14X176': [51.7, 2150.],
    'W14X211': [62.1, 2670.],
    'W14X246': [72.3, 3230.],
    'W14X287': [84.4, 3910.],
    'W24X110': [32.5, 3330.],
    'W24X130': [38.3, 4020.],
    'W24X160': [47.1, 5120.]
}

nodeTag = 1

# procedure to read
def ElasticBeamColumn(eleTag, iNode, jNode, sectType, E, transfTag, M, massType):
    found = 0
    prop = WSection[sectType]

    A = prop[0]
    I = prop[1]
    element('elasticBeamColumn', eleTag, iNode, jNode, A, E, I, transfTag, 'mass', M, massType)

# add nodes
# - floor at a time
yLoc = 0.
for j in range(0, numFloor + 1):
    xLoc = 0.
    for i in range(0, numBay + 1):
        node(nodeTag, xLoc, yLoc)
        xLoc += bayWidth
        nodeTag += 1

    if j < numFloor:
        storyHeight = storyHeights[j]

    yLoc += storyHeight

# fix first floor
fix(1, 1, 1, 1)
fix(2, 1, 1, 1)
fix(3, 1, 1, 1)

# rigid floor constraint & masses
nodeTagR = 5
nodeTag = 4
for j in range(1, numFloor + 1):
    for i in range(0, numBay + 1):
        if nodeTag != nodeTagR:
            equalDOF(nodeTagR, nodeTag, 1)
        else:
            mass(nodeTagR, massX, 1.0e-10, 1.0e-10)

        nodeTag += 1

    nodeTagR += numBay + 1

geomTransf(coordTransf, 1)

# add columns
eleTag = 1
for j in range(0, numBay + 1):
    end1 = j + 1
    end2 = end1 + numBay + 1
    thisColumn = columns[j]

    for i in range(0, numFloor):
        secType = thisColumn[i]
        ElasticBeamColumn(eleTag, end1, end2, secType, E, 1, M, massType)
        end1 = end2
        end2 += numBay + 1
        eleTag += 1

# add beams
for j in range(1, numFloor + 1):
    end1 = (numBay + 1) * j + 1
    end2 = end1 + 1
    secType = beams[j - 1]
    for i in range(0, numBay):
        ElasticBeamColumn(eleTag, end1, end2, secType, E, 1, M, massType)
        end1 = end2
        end2 = end1 + 1
        eleTag += 1

# calculate eigenvalues & print results
numEigen = 7
eigenValues = eigen(numEigen)
PI = 2 * asin(1.0)

# plot model
# Display Model
plot_model()
# Display specific mode shape
plot_modeshape(1)

# apply load for static analysis & perform analysis
timeSeries('Linear', 1)
pattern('Plain', 1, 1)
load(22, 20.0, 0., 0.)
load(19, 15.0, 0., 0.)
load(16, 12.5, 0., 0.)
load(13, 10.0, 0., 0.)
load(10, 7.5, 0., 0.)
load(7, 5.0, 0., 0.)
load(4, 2.5, 0., 0.)

integrator('LoadControl', 1.0)
algorithm('Linear')
analysis('Static')
analyze(1)

# determine Pass/Failure of the test
ok = 0

#
# print pretty output of comparisons
#

#               SAP2000   SeismoStruct
comparisonResults = [[1.2732, 0.4313, 0.2420, 0.1602, 0.1190, 0.0951, 0.0795],
                     [1.2732, 0.4313, 0.2420, 0.1602, 0.1190, 0.0951, 0.0795]]

print("\n\nPeriod Comparison:")
print('{:>10}{:>15}{:>15}{:>15}'.format('Period', 'OppenSees', 'SAP2000', 'SeisoStruct'))

# format string
for i in range(0, numEigen):
    lamb = eigenValues[i]
    period = 2 * PI / sqrt(lamb)
    print('{:>10}{:>15.5f}{:>15.4f}{:>15.4f}'.format(i+1, period, comparisonResults[0][i], comparisonResults[1][i]))
    resultOther = comparisonResults[0][i]
    if abs(period - resultOther) > 9.99e-5:
        ok - 1

# print table of comparison
#       Parameter          SAP2000   SeismoStruct
comparisonResult = [["Disp Top", "Axial Force Bottom Left", "Moment Bottom Left"],
                    [1.45076, 69.99, 2324.68],
                    [1.451, 70.01, 2324.71]]
tolerance = [9.99e-6, 9.99e-3, 9.99e-3]

print("\n\nStatic Analysis Result Comparison:")
print('{:>30}{:>15}{:>15}{:>15}'.format('Parameter', 'OpenSees', 'SAP2000', 'SeismoStruct'))
for i in range(3):
    response = eleResponse(1, 'force')
    if i == 0:
        result = nodeDisp(22, 1)
    elif i == 1:
        result = abs(response[1])
    else:
        result = response[2]

    print('{:>30}{:>15.3f}{:>15.2f}{:>15.2f}'.format(comparisonResult[0][i],
                                                     result,
                                                     comparisonResult[1][i],
                                                     comparisonResult[2][i]))
    resultOther = comparisonResult[1][i]
    tol = tolerance[i]
    if abs(result - resultOther) > tol:
        ok - 1
        print("Failed->", i, abs(result - resultOther), tol)

    if ok == 0:
        print("PASSED Verification Test PortalFrame2d.py \n\n")
    else:
        print("FAILED Verification Test PortalFrame2d.py \n\n")
        

    

















    
