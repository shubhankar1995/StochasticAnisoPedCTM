"""
module: mapGeoToCells
-------------------------

Python Script for generating the input files for the StochasticAnisoPedCTM through an 
automated method using data available from Openstreetmap.org. This implemetation uses 
the YenKShortestPaths algorithm to compute various route options that are available 
to a pedestrian to travel from one point to another. The data from OpenStreetMap is 
converted from Graph form to a form that represents the actual street view with various
cell segregations which represents various blocks of space on the street connected 
with each other to form a street network. This street the network is used by 
StochasticAnisoPedCTM to simulate the pedestrian movement pattern.

Author: Shubhankar Mathur
"""

import pandas as pd
import numpy as np
from math import ceil, sqrt
import os
import csv
import datetime as dt
from copy import deepcopy
import random as rd

import osmnx as ox
import networkx as nx
from YenKShortestPaths import YenKShortestPaths

#Parameters impacting the radius of input data
DISTANCE_RANGE = 350                #radius of input area in meters
START_POINT = (-34.01746,151.06285) #lat,long
MAX_ROUTES = 3                      #NUmber of route options

#File Input Directory
odMatrixFileNamePath = "ODMatrix.txt"

#File Output name
CELL_FILE_NAME = "new_cells"
BLOCKAGE_FILE_NAME = "new_blockage"
DEMAND_FILE_NAME = "new_demand"
ROUTE_FILE_NAME = "new_route"
LINKS_FILE_NAME = "new_links"

#File Output Directory             
FILE_CREATION_PATH_CELLS = ""           #Current (root) directory by default
FILE_CREATION_PATH_BLOCKAGE = ""
FILE_CREATION_PATH_DEMAND = ""
FILE_CREATION_PATH_ROUTE = ""
FILE_CREATION_PATH_LINKS = ""

#DO NOT CHANGE VALUE OF ANY VARIABLE BEYOND THIS POINT UNLESS MODIFYING THE CODE
#constant values
FILE_FORMAT = ".txt"
SURFACE_AREA_CELL = 2.25
CELL_EDGE_LENGTH = 1
NUM_CELLS_PER_WIDTH = 2
NUM_CELLS_PER_ZONE = NUM_CELLS_PER_WIDTH * 2
MULT_FACTOR = 10000000
ROUTE_CONV_NAME = 'RT'

TIME_INCREMENT = 0.3
TRAVEL_TIME = 10.6

STRAIGHT_LENGTH = 1.5
TURN_LENGTH = 1.0607
BI_DIRECTION = 'true'

NEW_MAX_CORD = 50
NEW_MIN_CORD = 0

print("Generate Data.....Do not close the window")

#Function will create the dictionary which will store all the data related to cells
def createCells(node_list, lat_List, lon_list, node_length, node_link_list, node_coordinates):
    global NUM_CELLS_PER_ZONE
    cells_dict = {'cellName':[], 'zone':[], 'surfaceSize':[], 'coordinate':[]}
    node_serial = 1
    zone_serial = 1
    lat_min_par, long_min_par, lat_max_par, long_max_par = getNormalizeParameter(lat_list, lon_list)
    for node in node_link_list:
        tot_count = int(getCellCount(node))
        display_tot_count = round(tot_count/20)
        if display_tot_count%2 == 1:
            display_tot_count = display_tot_count + 1
        if display_tot_count == 0:
            display_tot_count = 2
        for i in range(display_tot_count):    #for 150 - 4 and 0.005
            cell_Name = getCellName(str(node[0]) + str(node[1]) ,i)
            cells_dict['cellName'].append(cell_Name)
            cells_dict['zone'].append(getZoneName(str(node[0]) + str(node[1]) ,ceil(i//NUM_CELLS_PER_ZONE)))
            cells_dict['surfaceSize'].append(getSurfaceArea())
            cells_dict['coordinate'].append(getCoordinates(lat_min_par, long_min_par, node, node_coordinates, i, display_tot_count))
    return cells_dict

#Function to translate the geo-pane distance to coordinate pane length
def translateLength(node):
    length = list(node_length[(node_length['u'] == node[0]) & (node_length['v'] == node[1])]["length"])[0]
    global CELL_EDGE_LENGTH
    translatedLength = (length // CELL_EDGE_LENGTH) * CELL_EDGE_LENGTH
    return translatedLength

#Get the number of cells for each path between 2 nodes
def getCellCount(node):
    global CELL_EDGE_LENGTH
    global NUM_CELLS_PER_WIDTH
    count = ((translateLength(node))//CELL_EDGE_LENGTH) * NUM_CELLS_PER_WIDTH
    return count

#Get the cell name
def getCellName(osmId, serial):
    #Convention: C<osmnxId><serial num>
    cellName = 'C' + str(osmId) + str(serial)
    return cellName

#Get the zone name
def getZoneName(cellName, serial):
    #Convention: Z<cellName><serial num>
    zoneName = 'Z' + cellName + str(serial)
    return zoneName

def getSurfaceArea():
    global SURFACE_AREA_CELL
    return SURFACE_AREA_CELL

#Get the coordinate points for each cell
def getCoordinates(lat_min, long_min, node, node_coordinates, serial_num, tot_count):
    #each block is defined as 1.5 units in length  "(-1.5|0) (0|0) (0|1.5) (-1.5|1.5)"
    lat1 = list(node_coordinates[node_coordinates['osmid']==node[0]]['x'])[0]
    lon1 = list(node_coordinates[node_coordinates['osmid']==node[0]]['y'])[0]
    lat2 = list(node_coordinates[node_coordinates['osmid']==node[1]]['x'])[0]
    lon2 = list(node_coordinates[node_coordinates['osmid']==node[1]]['y'])[0]
    length = list(node_length[(node_length['u'] == node[0]) & (node_length['v'] == node[1])]["length"])[0]
    nor_lat1, nor_lon1 = getNormalizedCoordinates(lat_min, long_min, lat1, lon1)
    nor_lat2, nor_lon2 = getNormalizedCoordinates(lat_min, long_min, lat2, lon2)
    distance = getDistance(nor_lat1, nor_lon1, nor_lat2, nor_lon2)
    MULTIPLI = 0.001
    nor_lat1 = nor_lat1* MULTIPLI #  (length/distance)
    nor_lon1 = nor_lon1* MULTIPLI #  (length/distance)
    nor_lat2 = nor_lat2* MULTIPLI #  (length/distance)
    nor_lon2 = nor_lon2* MULTIPLI #  (length/distance)
    distance = getDistance(nor_lat1, nor_lon1, nor_lat2, nor_lon2)
    if distance == 0:
        return
    slope = getSlope(nor_lat1, nor_lon1, nor_lat2, nor_lon2)
    dx1, dy1 = getDivisionPoint((serial_num//2), nor_lat1, nor_lon1, nor_lat2, nor_lon2, ceil(tot_count/2))
    dx2, dy2 = getDivisionPoint((serial_num//2) + 1, nor_lat1, nor_lon1, nor_lat2, nor_lon2, ceil(tot_count/2))
    px1, py1 = getPerprndicularCoordinates(dx1, dy1, slope, serial_num)
    px2, py2 = getPerprndicularCoordinates(dx2, dy2, slope, serial_num)
    #padding of 2 units to avoid negative coordinates
    cord = '(' + str(dx1+2) + '|' + str(dy1+2) +')' + ' (' + str(px1+2) + '|' + str(py1+2) +')' + ' (' + str(px2+2) + '|' + str(py2+2) +')' + ' (' + str(dx2+2) + '|' + str(dy2+2) +')'
    return cord

#Normalize geo-coordinates to fit the cartesian plane 
def getNormalizedCoordinates(lat_min, long_min, lat, lon):
    global MULT_FACTOR
    nor_lat = ((abs(lat) - abs(lat_min))*MULT_FACTOR)
    nor_lon = ((abs(lon) - abs(long_min))*MULT_FACTOR)
    return nor_lat, nor_lon

#Distance between 2 points in cartesian plane
def getDistance(x1, y1, x2, y2):
    distance = sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return distance

#Slope between 2 points in cartesian plane
def getSlope(x1, y1, x2, y2):
    slope = (y2 - y1)/(x2 - x1)
    perpendicularSlope = (1/slope)*(-1)
    return perpendicularSlope

#Get the min-max coordinates for normalization (shift origin to (0,0))
def getNormalizeParameter(lat_List, lon_List):
    lat_min = 0
    long_min = 0
    lat_max = 0
    long_max = 0
    if lat_list[0] > 0 :
        lat_min = min(lat_List)
        lat_max = max(lat_List)
    else:
        lat_min = max(lat_List)
        lat_max = min(lat_List)
    if lon_list[0] > 0:
        long_min = min(lon_List)
        long_max = max(lon_List)
    else:
        long_min = max(lon_List) #longitudes are in -tives
        long_max = min(lon_List)
    return lat_min, long_min, lat_max, long_max

#Get the edge coordinates of the cells perpendicular  to central line joining the 2 nodes
def getPerprndicularCoordinates(x1, y1, slope, serial_num):
    a = slope**2 + 1
    b = (slope**2 + 1)*y1*(-2)
    c = ((slope**2 + 1)*(y1**2)) - ((slope**2)*(CELL_EDGE_LENGTH**2))
    if serial_num%2 == 0:
        y_sol = ((-1)*b + sqrt(b**2 - 4*a*c))/(2*a)
        x_sol = ((y_sol - y1)/slope) + x1
    else:
        y_sol = ((-1)*b - sqrt(b**2 - 4*a*c))/(2*a)
        x_sol = ((y_sol - y1)/slope) + x1
    return x_sol, y_sol

#Get the edges of cell that fall on the central line joining the 2 nodes
def getDivisionPoint(part, x1, y1, x2, y2, tot_count):
    dx = ((part*x2) + ((tot_count - part)*x1))/tot_count
    dy = ((part*y2) + ((tot_count - part)*y1))/tot_count
    return dx, dy

#Get the street data from the Open Street Map library
G4 = ox.graph_from_point(START_POINT,distance=DISTANCE_RANGE, distance_type='network', network_type='walk')
graph = deepcopy(G4)

#Convert data into graphs
data = ox.save_load.graph_to_gdfs(G4, nodes=True, edges=True, node_geometry=False, fill_edge_geometry=False)

node_coordinates = data[0][["osmid","x","y"]]       #output is pandas framework, x is lat, y is long 
node_length = data[1][["u","v","length","oneway"]]  #output is pandas framework u and v are osmids for the nodes

lat_list = []
lon_list = []
node_list = []

node_link_list = list((G4.to_undirected()).edges())

for index, rows in node_coordinates.iterrows():
    lat_list.append(rows.x)
    lon_list.append(rows.y)
    node_list.append(int(rows.osmid))

cells_dict = createCells(node_list, lat_list, lon_list, node_length, node_link_list, node_coordinates)

cell_data = pd.DataFrame.from_dict(cells_dict)

#Generate the cell Data
cell_data.to_csv(os.path.join(FILE_CREATION_PATH_CELLS, CELL_FILE_NAME + FILE_FORMAT), index=False)

# ------------------------------------ Blockage File ------------------------------------------------------#

blockage_dict = {'cellName':[], 'startTime':[], 'endTime':[], 'percentage':[]}

#Defalt is set to 0% blockage and 0 as start and end time in seconds
blockage_dict['cellName'] = cells_dict['cellName']
blockage_dict['startTime'] = [0 for _ in range(len(blockage_dict['cellName']))]
blockage_dict['endTime'] = [0 for _ in range(len(blockage_dict['cellName']))]
blockage_dict['percentage'] = [0 for _ in range(len(blockage_dict['cellName']))]

blockage_data = pd.DataFrame.from_dict(blockage_dict)

#Generate the cell blockage list file
blockage_data.to_csv(os.path.join(FILE_CREATION_PATH_BLOCKAGE, BLOCKAGE_FILE_NAME  + FILE_FORMAT), index=False)

# -------------------------- Code for generating the links -------------------------------------------------#

links_dict = {'cellName':[], 'origCellName':[], 'destCellName':[], 'length':[], 'streamOrig':[], 'streamDest':[], 'boolean bi-directional':[]}

#Check if a particular cell exists in the system
def isCellExists(cellName):
    if cellName in cells_dict['cellName']:
        return True
    return False

#Generate the data related to links connecting the cells in a path
def createLinksData(node_list):
    temp_list = []
    for i in range(len(node_list) -1):
        tmp1 = str(node_list[i]) + str(node_list[i+1])
        tmp2 = str(node_list[i+1]) + str(node_list[i])
        tmp = tmp1
        count = cell_data[cell_data['cellName'].str[1:len(tmp1)+1]==tmp1].zone.count()
        if count == 0:
            count = cell_data[cell_data['cellName'].str[1:len(tmp2)+1]==tmp2].zone.count()
            tmp = tmp2
        # for staright line path x-x-x 
        for j in range(count):                           # ending with -2 to keep the dest within the limit of count
            if (isCellExists('C'+tmp+str(j+2)) and isCellExists('C'+tmp+str(j)) and isCellExists('C'+tmp+str(j+4))):
                links_dict['cellName'].append('C'+tmp+str(j+2))
                links_dict['origCellName'].append('C'+tmp+str(j))
                links_dict['destCellName'].append('C'+tmp+str(j+4))
                links_dict['length'].append(STRAIGHT_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
        # for curving down path x-x
        #                         |
        #                         x
        for j in range(1, count, 2):                           # starting with 1 since the origin is not in -ve, for odd j
            if (isCellExists('C'+tmp+str(j+2)) and isCellExists('C'+tmp+str(j)) and isCellExists('C'+tmp+str(j+1))):
                links_dict['cellName'].append('C'+tmp+str(j+2))
                links_dict['origCellName'].append('C'+tmp+str(j))
                links_dict['destCellName'].append('C'+tmp+str(j+1))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('S')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
        #                       x
        #                       |
        # for curving up path x-x
        for j in range(0, count, 2):                           # for even j
            if (isCellExists('C'+tmp+str(j+2)) and isCellExists('C'+tmp+str(j)) and isCellExists('C'+tmp+str(j+3))):
                links_dict['cellName'].append('C'+tmp+str(j+2))
                links_dict['origCellName'].append('C'+tmp+str(j))
                links_dict['destCellName'].append('C'+tmp+str(j+3))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('N')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
        #                     x
        #                     |
        # for curving up path x-x
        for j in range(1, count, 2):                           # starting with 1 since the origin is not in -ve, for odd j
            if (isCellExists('C'+tmp+str(j-1)) and isCellExists('C'+tmp+str(j)) and isCellExists('C'+tmp+str(j+1))):
                links_dict['cellName'].append('C'+tmp+str(j-1))
                links_dict['origCellName'].append('C'+tmp+str(j))
                links_dict['destCellName'].append('C'+tmp+str(j+1))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('N')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
        # for curving down path x-x
        #                       |
        #                       x
        for j in range(0, count, 2):                           # for even j
            if (isCellExists('C'+tmp+str(j+1)) and isCellExists('C'+tmp+str(j)) and isCellExists('C'+tmp+str(j+3))):
                links_dict['cellName'].append('C'+tmp+str(j+1))
                links_dict['origCellName'].append('C'+tmp+str(j))
                links_dict['destCellName'].append('C'+tmp+str(j+3))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('S')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)

#Generate the data related to links connecting the cells of 2 different path in a route
def createRoadIntersections(node_list):
    temp_list = []
    for i in range(len(node_list) -2):
        isReverse1 = 0
        isReverse2 = 0
        tmp1 = str(node_list[i]) + str(node_list[i+1])
        tmp2 = str(node_list[i+1]) + str(node_list[i])
        tmp_1 = tmp1
        count_1 = cell_data[cell_data['cellName'].str[1:len(tmp1)+1]==tmp1].zone.count()
        if count_1 == 0:
            count_1 = cell_data[cell_data['cellName'].str[1:len(tmp2)+1]==tmp2].zone.count()
            tmp_1 = tmp2
            isReverse1 = 1
        tmp3 = str(node_list[i+1]) + str(node_list[i+2])
        tmp4 = str(node_list[i+2]) + str(node_list[i+1])
        tmp_2 = tmp3
        count_2 = cell_data[cell_data['cellName'].str[1:len(tmp3)+1]==tmp3].zone.count()
        if count_2 == 0:
            count_2 = cell_data[cell_data['cellName'].str[1:len(tmp4)+1]==tmp4].zone.count()
            tmp_2 = tmp4
            isReverse2 = 1
        if isReverse1 == 0 and isReverse2 == 0:
            #case1-a
            if (isCellExists('C'+tmp_1+str(count_1-1)) and isCellExists('C'+tmp_1+str(count_1-3)) and isCellExists('C'+tmp_2+str(1))):
                links_dict['cellName'].append('C'+tmp_1+str(count_1-1))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-3))
                links_dict['destCellName'].append('C'+tmp_2+str(1))
                links_dict['length'].append(STRAIGHT_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case1-b
            if (isCellExists('C'+tmp_1+str(count_1-2)) and isCellExists('C'+tmp_1+str(count_1-4)) and isCellExists('C'+tmp_2+str(0))):
                links_dict['cellName'].append('C'+tmp_1+str(count_1-2))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-4))
                links_dict['destCellName'].append('C'+tmp_2+str(0))
                links_dict['length'].append(STRAIGHT_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case2
            if (isCellExists('C'+tmp_2+str(0)) and isCellExists('C'+tmp_1+str(count_1-2)) and isCellExists('C'+tmp_2+str(1))):
                links_dict['cellName'].append('C'+tmp_2+str(0))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-2))
                links_dict['destCellName'].append('C'+tmp_2+str(1))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('N')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case3
            if (isCellExists('C'+tmp_2+str(1)) and isCellExists('C'+tmp_1+str(count_1-1)) and isCellExists('C'+tmp_2+str(0))):
                links_dict['cellName'].append('C'+tmp_2+str(1))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-1))
                links_dict['destCellName'].append('C'+tmp_2+str(0))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('S')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case4
            if (isCellExists('C'+tmp_1+str(count_1-2)) and isCellExists('C'+tmp_1+str(count_1-1)) and isCellExists('C'+tmp_2+str(0))):
                links_dict['cellName'].append('C'+tmp_1+str(count_1-2))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-1))
                links_dict['destCellName'].append('C'+tmp_2+str(0))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('N')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case5
            if (isCellExists('C'+tmp_1+str(count_1-1)) and isCellExists('C'+tmp_1+str(count_1-2)) and isCellExists('C'+tmp_2+str(1))):
                links_dict['cellName'].append('C'+tmp_1+str(count_1-1))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-2))
                links_dict['destCellName'].append('C'+tmp_2+str(1))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('S')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
        if isReverse1 == 1 and isReverse2 == 0:
            #case1-a
            if (isCellExists('C'+tmp_1+str(1)) and isCellExists('C'+tmp_1+str(3)) and isCellExists('C'+tmp_2+str(1))):
                links_dict['cellName'].append('C'+tmp_1+str(1))
                links_dict['origCellName'].append('C'+tmp_1+str(3))
                links_dict['destCellName'].append('C'+tmp_2+str(1))
                links_dict['length'].append(STRAIGHT_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case1-b
            if (isCellExists('C'+tmp_1+str(0)) and isCellExists('C'+tmp_1+str(2)) and isCellExists('C'+tmp_2+str(0))):
                links_dict['cellName'].append('C'+tmp_1+str(0))
                links_dict['origCellName'].append('C'+tmp_1+str(2))
                links_dict['destCellName'].append('C'+tmp_2+str(0))
                links_dict['length'].append(STRAIGHT_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case2
            if (isCellExists('C'+tmp_2+str(0)) and isCellExists('C'+tmp_1+str(0)) and isCellExists('C'+tmp_2+str(1))):
                links_dict['cellName'].append('C'+tmp_2+str(0))
                links_dict['origCellName'].append('C'+tmp_1+str(0))
                links_dict['destCellName'].append('C'+tmp_2+str(1))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('N')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case3
            if (isCellExists('C'+tmp_2+str(1)) and isCellExists('C'+tmp_1+str(1)) and isCellExists('C'+tmp_2+str(0))):
                links_dict['cellName'].append('C'+tmp_2+str(1))
                links_dict['origCellName'].append('C'+tmp_1+str(1))
                links_dict['destCellName'].append('C'+tmp_2+str(0))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('S')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case4
            if (isCellExists('C'+tmp_1+str(0)) and isCellExists('C'+tmp_1+str(1)) and isCellExists('C'+tmp_2+str(0))):
                links_dict['cellName'].append('C'+tmp_1+str(0))
                links_dict['origCellName'].append('C'+tmp_1+str(1))
                links_dict['destCellName'].append('C'+tmp_2+str(0))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('N')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case5
            if (isCellExists('C'+tmp_1+str(0)) and isCellExists('C'+tmp_1+str(1)) and isCellExists('C'+tmp_2+str(1))):
                links_dict['cellName'].append('C'+tmp_1+str(1))
                links_dict['origCellName'].append('C'+tmp_1+str(0))
                links_dict['destCellName'].append('C'+tmp_2+str(1))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('S')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
        if isReverse1 == 0 and isReverse2 == 1:
            #case1-a
            if (isCellExists('C'+tmp_1+str(count_1-1)) and isCellExists('C'+tmp_1+str(count_1-3)) and isCellExists('C'+tmp_2+str(count_2-1))):
                links_dict['cellName'].append('C'+tmp_1+str(count_1-1))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-3))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-1))
                links_dict['length'].append(STRAIGHT_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case1-b
            if (isCellExists('C'+tmp_1+str(count_1-2)) and isCellExists('C'+tmp_1+str(count_1-4)) and isCellExists('C'+tmp_2+str(count_2-2))):
                links_dict['cellName'].append('C'+tmp_1+str(count_1-2))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-4))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-2))
                links_dict['length'].append(STRAIGHT_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case2
            if (isCellExists('C'+tmp_2+str(count_2-2)) and isCellExists('C'+tmp_1+str(count_1-2)) and isCellExists('C'+tmp_2+str(count_2-1))):
                links_dict['cellName'].append('C'+tmp_2+str(count_2-2))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-2))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-1))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('N')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case3
            if (isCellExists('C'+tmp_2+str(count_2-1)) and isCellExists('C'+tmp_1+str(count_1-1)) and isCellExists('C'+tmp_2+str(count_2-2))):
                links_dict['cellName'].append('C'+tmp_2+str(count_2-1))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-1))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-2))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('S')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case4
            if (isCellExists('C'+tmp_1+str(count_1-1)) and isCellExists('C'+tmp_1+str(count_1-2)) and isCellExists('C'+tmp_2+str(count_2-2))):
                links_dict['cellName'].append('C'+tmp_1+str(count_1-1))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-2))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-2))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('N')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case5
            if (isCellExists('C'+tmp_1+str(count_1-1)) and isCellExists('C'+tmp_1+str(count_1-2)) and isCellExists('C'+tmp_2+str(count_2-2))):
                links_dict['cellName'].append('C'+tmp_1+str(count_1-1))
                links_dict['origCellName'].append('C'+tmp_1+str(count_1-2))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-2))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('S')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
        if isReverse1 == 1 and isReverse2 == 1:
            #case1-a
            if (isCellExists('C'+tmp_1+str(1)) and isCellExists('C'+tmp_1+str(3)) and isCellExists('C'+tmp_2+str(count_2-1))):
                links_dict['cellName'].append('C'+tmp_1+str(1))
                links_dict['origCellName'].append('C'+tmp_1+str(3))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-1))
                links_dict['length'].append(STRAIGHT_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case1-b
            if (isCellExists('C'+tmp_1+str(0)) and isCellExists('C'+tmp_1+str(2)) and isCellExists('C'+tmp_2+str(count_2-2))):
                links_dict['cellName'].append('C'+tmp_1+str(0))
                links_dict['origCellName'].append('C'+tmp_1+str(2))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-2))
                links_dict['length'].append(STRAIGHT_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case2
            if (isCellExists('C'+tmp_2+str(count_2-2)) and isCellExists('C'+tmp_1+str(0)) and isCellExists('C'+tmp_2+str(count_2-1))):
                links_dict['cellName'].append('C'+tmp_2+str(count_2-2))
                links_dict['origCellName'].append('C'+tmp_1+str(0))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-1))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('N')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case3
            if (isCellExists('C'+tmp_2+str(count_2-1)) and isCellExists('C'+tmp_1+str(1)) and isCellExists('C'+tmp_2+str(count_2-2))):
                links_dict['cellName'].append('C'+tmp_2+str(count_2-1))
                links_dict['origCellName'].append('C'+tmp_1+str(1))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-2))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('W')
                links_dict['streamDest'].append('S')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case4
            if (isCellExists('C'+tmp_1+str(0)) and isCellExists('C'+tmp_1+str(1)) and isCellExists('C'+tmp_2+str(count_2-2))):
                links_dict['cellName'].append('C'+tmp_1+str(0))
                links_dict['origCellName'].append('C'+tmp_1+str(1))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-2))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('N')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)
            #case5
            if (isCellExists('C'+tmp_1+str(1)) and isCellExists('C'+tmp_1+str(0)) and isCellExists('C'+tmp_2+str(count_2-1))):
                links_dict['cellName'].append('C'+tmp_1+str(1))
                links_dict['origCellName'].append('C'+tmp_1+str(0))
                links_dict['destCellName'].append('C'+tmp_2+str(count_2-1))
                links_dict['length'].append(TURN_LENGTH)
                links_dict['streamOrig'].append('S')
                links_dict['streamDest'].append('E')
                links_dict['boolean bi-directional'].append(BI_DIRECTION)

#Generate the data related to links connecting the origin and destination cells
def createPathEnds(node_list):
    #origin cells
    tmp1 = str(node_list[0]) + str(node_list[1])
    tmp2 = str(node_list[1]) + str(node_list[0])
    isReverse = 0
    tmp_1 = tmp1
    count_1 = cell_data[cell_data['cellName'].str[1:len(tmp1)+1]==tmp1].zone.count()
    if count_1 == 0:
        count_1 = cell_data[cell_data['cellName'].str[1:len(tmp2)+1]==tmp2].zone.count()
        tmp_1 = tmp2
        isReverse = 1
    if isReverse == 0:
        if (isCellExists('C'+tmp_1+str(0)) and isCellExists('C'+tmp_1+str(2))):
            links_dict['cellName'].append('C'+tmp_1+str(0))
            links_dict['origCellName'].append('none')
            links_dict['destCellName'].append('C'+tmp_1+str(2))
            links_dict['length'].append('MIN')
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('E')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)
        if (isCellExists('C'+tmp_1+str(1)) and isCellExists('C'+tmp_1+str(3))):
            links_dict['cellName'].append('C'+tmp_1+str(1))
            links_dict['origCellName'].append('none')
            links_dict['destCellName'].append('C'+tmp_1+str(3))
            links_dict['length'].append('MIN')
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('E')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)
    else:
        if (isCellExists('C'+tmp_1+str(count_1 - 1)) and isCellExists('C'+tmp_1+str(count_1 - 3))):
            links_dict['cellName'].append('C'+tmp_1+str(count_1 - 1))
            links_dict['origCellName'].append('none')
            links_dict['destCellName'].append('C'+tmp_1+str(count_1 - 3))
            links_dict['length'].append('MIN')
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('E')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)
        if (isCellExists('C'+tmp_1+str(count_1 - 2)) and isCellExists('C'+tmp_1+str(count_1 - 4))):
            links_dict['cellName'].append('C'+tmp_1+str(count_1 - 2))
            links_dict['origCellName'].append('none')
            links_dict['destCellName'].append('C'+tmp_1+str(count_1 - 4))
            links_dict['length'].append('MIN')
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('E')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)
    #cell destination
    tmp1 = str(node_list[len(node_list)-2]) + str(node_list[len(node_list)-1])
    tmp2 = str(node_list[len(node_list)-1]) + str(node_list[len(node_list)-2])
    isReverse = 0
    tmp_1 = tmp1
    count_1 = cell_data[cell_data['cellName'].str[1:len(tmp1)+1]==tmp1].zone.count()
    if count_1 == 0:
        count_1 = cell_data[cell_data['cellName'].str[1:len(tmp2)+1]==tmp2].zone.count()
        tmp_1 = tmp2
        isReverse = 1
    if isReverse == 0:
        if (isCellExists('C'+tmp_1+str(0)) and isCellExists('C'+tmp_1+str(2))):
            links_dict['cellName'].append('C'+tmp_1+str(count_1 - 1))
            links_dict['origCellName'].append('C'+tmp_1+str(count_1 - 3))
            links_dict['destCellName'].append('none')
            links_dict['length'].append('MIN')
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('E')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)
        if (isCellExists('C'+tmp_1+str(1)) and isCellExists('C'+tmp_1+str(3))):
            links_dict['cellName'].append('C'+tmp_1+str(count_1 - 2))
            links_dict['origCellName'].append('C'+tmp_1+str(count_1 - 4))
            links_dict['destCellName'].append('none')
            links_dict['length'].append('MIN')
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('E')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)
    else:
        if (isCellExists('C'+tmp_1+str(0)) and isCellExists('C'+tmp_1+str(2))):
            links_dict['cellName'].append('C'+tmp_1+str(0))
            links_dict['origCellName'].append('C'+tmp_1+str(2))
            links_dict['destCellName'].append('none')
            links_dict['length'].append('MIN')
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('E')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)
        if (isCellExists('C'+tmp_1+str(1)) and isCellExists('C'+tmp_1+str(3))):
            links_dict['cellName'].append('C'+tmp_1+str(1))
            links_dict['origCellName'].append('C'+tmp_1+str(3))
            links_dict['destCellName'].append('none')
            links_dict['length'].append('MIN')
            links_dict['streamOrig'].append('W')
            links_dict['streamDest'].append('E')
            links_dict['boolean bi-directional'].append(BI_DIRECTION)

# -------------------------- Code for finding the routes -------------------------------------------------#

routes_data_dict = {'routeName':[],'zoneSequence':[], 'distance':[]}

# Get the list of zones which are part of the route
def getZoneSequence(node_list):
    temp_list = []
    for i in range(len(node_list) -1):
        flagRev = 0
        tmp1 = str(node_list[i]) + str(node_list[i+1])
        tmp2 = str(node_list[i+1]) + str(node_list[i])
        tmp = tmp1
        count = ceil(cell_data[cell_data['cellName'].str[1:len(tmp1)+1]==tmp1].zone.count() / 4)
        if count == 0:
            count = ceil(cell_data[cell_data['cellName'].str[1:len(tmp2)+1]==tmp2].zone.count() / 4)
            tmp = tmp2
            flagRev = 1
        if flagRev == 0:
            for j in range(count):
                temp_list.append('Z'+tmp+str(j))
        else:
            for j in range(count-1,-1,-1):
                temp_list.append('Z'+tmp+str(j))
    return '-'.join(str(val) for val in temp_list)

#Get the data related to routes between source and destination nodes 
def getRouteData(orig_cord, dest_cord, serial_num):
    orig_node = ox.get_nearest_node(G4, (float(orig_cord.split('|')[0]), float(orig_cord.split('|')[1])))
    dest_node = ox.get_nearest_node(G4, (float(dest_cord.split('|')[0]), float(dest_cord.split('|')[1])))
    routes_dict = {'routeName':[],'zoneSequence':[], 'distance':[]}
    kShortestPaths = YenKShortestPaths(G4, orig_node, dest_node, 'length')
    for i in range(MAX_ROUTES):
        try:
            #get the cell names while finding the routes
            kShortestPathsObject = deepcopy(kShortestPaths.next())
            node_list = kShortestPathsObject.nodeList
            routes_dict['zoneSequence'].append(getZoneSequence(node_list))
            routes_dict['routeName'].append(ROUTE_CONV_NAME+str(serial_num)+str(i))
            routes_dict['distance'].append(kShortestPathsObject.cost)
            createLinksData(node_list)
            createRoadIntersections(node_list)
            createPathEnds(node_list)
        except:
            pass
    return routes_dict

#Merge the dictionaries of all the routes
def mergeRouteDataDict(routes_data_dict, routes_dict):
    for i in range(len(routes_dict['zoneSequence'])):
        routes_data_dict['zoneSequence'].append(routes_dict['zoneSequence'][i])
        routes_data_dict['routeName'].append(routes_dict['routeName'][i])
        routes_data_dict['distance'].append(routes_dict['distance'][i])
    return routes_data_dict

# -------------------------- Code for generating the Demand File -------------------------------------------------#
ODMatrixList = []

demand_dict = {'routeName':[], 'depTime':[], 'numPpl':[], 'travelTime':[], 'routeName2':[],'routeName3':[]}

#Normalize time from time format to interger
def getNormalizedTime(min_time, curr_time):
    temp_time = dt.datetime.strptime(curr_time, '%H:%M')
    nor_time  = (temp_time - min_time).seconds
    return nor_time

def getMinTime(ODMatrixList):
    min_time = dt.datetime.strptime('23:59:59', '%H:%M:%S') #highest possible time
    for row in ODMatrixList:
        temp_time = dt.datetime.strptime(row[2], '%H:%M')
        if min_time > temp_time:
            min_time = temp_time
    return min_time

#Read the OD Matrix data
with open(odMatrixFileNamePath, encoding="utf8") as dataFile:
    data = csv.reader(dataFile, delimiter=',')
    for row in data:
        if '#' not in row[0]:
            ODMatrixList.append(row)

min_time = getMinTime(ODMatrixList)

#Generate the Demand file data
serial_num = 0
for row in ODMatrixList:
    start_time = getNormalizedTime(min_time, row[2])
    demand = int(row[3])
    routes_dict = getRouteData(row[0], row[1], serial_num)
    routes_data_dict = mergeRouteDataDict(routes_data_dict, routes_dict)
    num_routes = len(routes_dict['routeName'])
    if num_routes >= 1:
        demand_dict['routeName'].append(routes_dict['routeName'][0])
    else:
        demand_dict['routeName'].append('NA')
    if num_routes >= 2:
        demand_dict['routeName2'].append(routes_dict['routeName'][1])           #changes made here for testing
    else:
        demand_dict['routeName2'].append('NA')
    if num_routes >= 3:
        demand_dict['routeName3'].append(routes_dict['routeName'][2])
    else:
        demand_dict['routeName3'].append('NA')
    demand_dict['numPpl'].append(str(demand))
    demand_dict['depTime'].append(str(start_time))
    demand_dict['travelTime'].append(str(TRAVEL_TIME))
    serial_num = serial_num + 1

#Generate the demand file
demand_data = pd.DataFrame.from_dict(demand_dict)
demand_data.to_csv(os.path.join(FILE_CREATION_PATH_DEMAND, DEMAND_FILE_NAME + FILE_FORMAT), index=False)

#Generate the route file
route_data = pd.DataFrame.from_dict(routes_data_dict)
route_data.to_csv(os.path.join(FILE_CREATION_PATH_ROUTE, ROUTE_FILE_NAME + FILE_FORMAT), index=False)

#Generate the link file
links_data = pd.DataFrame.from_dict(links_dict)
links_data = links_data.drop_duplicates()
links_data.to_csv(os.path.join(FILE_CREATION_PATH_LINKS, LINKS_FILE_NAME + FILE_FORMAT), index=False)

print("All files generated")