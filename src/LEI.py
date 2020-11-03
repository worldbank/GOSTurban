import os, sys, logging

import geojson, rasterio
import rasterio.features

import pandas as pd
import numpy as np

from shapely.geometry import shape, GeometryCollection
from shapely.wkt import loads

def calculate_LEI(inputGHSL, old_list = [4,5,6], new_list=[3]):
    ''' Calculate LEI using vector objects in rasterio
    
    INPUT
    inputGHSL [string] - path the GHSL raster object
    [optional] old_list [list of numbers] - values in GHSL to consider old urban
    [optional] new_list [int] - value in GHSL to consider new urban
    '''
    inRaster = rasterio.open(inputGHSL)
    inR = inRaster.read()

    newR = (np.isin(inR, new_list)).astype('int')
    oldR = (np.isin(inR, old_list)).astype('int')
    allVals = []
    for geom, value in rasterio.features.shapes(newR.astype('uint8'), transform=inRaster.transform):
        if value == 1:
            # Convert the geom to a shape and buffer by 300 metres
            curShape = shape(geom)
            bufferArea = curShape.buffer(300)
            #Clip out the original shape to leave just the donut
            donutArea = bufferArea.difference(curShape)
            # Rasterize donut shape
            shapes = [(donutArea, 1)]
            burned = rasterio.features.rasterize(shapes=shapes, fill=0, 
                             out_shape=(oldR.shape[1], oldR.shape[2]), 
                             transform=inRaster.transform)
            # Multiply the new raster by the old urban data to get the total
            #     amount of old area in the buffer around the new urban area
            oldArea = (oldR[0,:,:] * burned).sum()
            totalArea = burned.sum()
            allVals.append([curShape, oldArea, totalArea])
    return(allVals)
    
def summarize_LEI(in_file, leap_val=0.01, exp_val=0.05):
    ''' Summarize the LEI csv files produced by calculate_LEI
    
    in_file [string path]: [path to csv file generated from the calculate_LEI above
    leap_val [float]: LEI value below which areas are considered to be leapfrog
    exp_val [float]: LEI value above which areas are considered to be expansion
    
    returns
    [pandas groupby row]
    
    example
    
    for res_file in all_results_files:
        res = summarize_LEI(res_file)
        baseName = os.path.basename(os.path.dirname(res_file))
        summarized_results[baseName] = res
    
    all_results = pd.DataFrame(summarized_results).transpose()
    '''
    res = pd.read_csv(in_file)
    res['area'] = res['geometry'].apply(lambda x: loads(x).area)
    def calculate_LEI(val, leap_val=0.01, exp_val=0.5):
        if val <= leap_val:
            return('Leapfrog')
        elif val < exp_val:
            return('Expansion')
        else:
            return('Infill')
    res['class'] = res['LEI'].apply(lambda x: calculate_LEI(x))
    xx = res.groupby('class')
    return(xx.sum()['area'])