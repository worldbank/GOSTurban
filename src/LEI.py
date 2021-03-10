import os, sys, logging

import geojson, rasterio
import rasterio.features

import pandas as pd
import numpy as np

from shapely.geometry import shape, GeometryCollection
from shapely.wkt import loads

def calculate_LEI(inputGHSL, old_list = [4,5,6], new_list=[3], buffer_dist=300):
    ''' Calculate LEI using vector objects in rasterio
    
    INPUT
    inputGHSL [string] - path the GHSL raster object
    [optional] old_list [list of numbers] - values in GHSL to consider old urban. 4, 5, 6 indicates change from 2000
    [optional] new_list [int] - value in GHSL to consider new urban. 3 indicates 2014
    
    RETURNS
    [array] - individual new built areas with LEI results. Each item is a single new built feature with three columns: 
                1. geometry of the new built area feature
                2. number of pixels in new built area donut from old built area
                3. area of new built area buffer
                
    EXAMPLE
        # This calculates the change from 1990 and 2000
        lei_raw = calculate_LEI(input_ghsl, old_list = [5,6], new_list=[4])
        lei_90_00 = pd.DataFrame(lei_raw, columns=['geometry', 'old', 'total'])
        lei_90_00['LEI'] = lei_90_00['old'] / lei_90_00['total']      
        lei_90_00.head()    
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
            bufferArea = curShape.buffer(buffer_dist)
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
    
def summarize_LEI(in_file, leap_val=0.05, exp_val=0.9):
    ''' Summarize the LEI csv files produced by calculate_LEI
    
    in_file [string path or datafrane]: generated from the calculate_LEI above
    leap_val [float]: LEI value below which areas are considered to be leapfrog
    exp_val [float]: LEI value above which areas are considered to be infill
    
    returns
    [pandas groupby row]
    
    example
    
    for res_file in all_results_files:
        res = summarize_LEI(res_file)
        baseName = os.path.basename(os.path.dirname(res_file))
        summarized_results[baseName] = res
    
    all_results = pd.DataFrame(summarized_results).transpose()
    '''
    if isinstance(in_file, str):
        res = pd.read_csv(in_file)
        res['area'] = res['geometry'].apply(lambda x: loads(x).area)
    else:
        res = in_file
        if not 'area' in res.columns:
            res['area'] = res['geometry'].apply(lambda x: x.area)
    
    def calculate_LEI(val, leap_val, exp_val):
        if val <= leap_val:
            return('Leapfrog')
        elif val < exp_val:
            return('Expansion')
        else:
            return('Infill')
    res['class'] = res['LEI'].apply(lambda x: calculate_LEI(x, leap_val, exp_val))
    xx = res.groupby('class')
    return(xx.sum()['area'])