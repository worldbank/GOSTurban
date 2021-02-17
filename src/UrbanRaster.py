#-------------------------------------------------------------------------------
# Calculate urban areas from gridded population data
# Benjamin P Stewart, April 2019
#   Purpose is to create high density urban clusters and urban cluster above minimum
#   density and total population thresholds
#-------------------------------------------------------------------------------

import os, sys, logging, geojson, json, time

import rasterio
import geopandas as gpd
import pandas as pd
import numpy as np

from scipy import stats
from scipy import ndimage
from scipy.ndimage import generic_filter
from scipy.sparse.csgraph import connected_components
from rasterio import features
from rasterio.features import rasterize
from shapely.geometry import shape, Polygon

'''prints the time along with the message'''
def tPrint(s):
    print("%s\t%s" % (time.strftime("%H:%M:%S"), s))

class urbanGriddedPop(object):
    def __init__(self, inRaster):
        """
        Create urban definitions using gridded population data.
        
        :param inRaster: string or rasterio object representing gridded population data        
        """
        if type(inRaster) == str:
            self.inR = rasterio.open(inRaster)
        elif isinstance(inRaster, rasterio.DatasetReader):
            self.inR = inRaster
        else:
            raise(ValueError("Input raster dataset must be a file path or a rasterio object"))
            
    def calculateDegurba(self, urbDens=300, hdDens=1500, urbThresh=5000, hdThresh=50000, minPopThresh=50,
            out_raster = '', print_message='', verbose=False):
        ''' Calculate complete DEGURBA classification based on gridded population data
            https://ghsl.jrc.ec.europa.eu/degurbaDefinitions.php
            CLASSES:
            (30) Urban centre - dens: 1500, totalpop: 50000, smoothed
            (23) Urban cluster, town, dense urban cluster - dens: 1500, totalpop: >5000, <50000, not type 30
            (22) Urban cluster, town, semidense urban cluster - dens: 300, totalpop: >5000, farther than 3 km from 23 or another 22
            (21) Urban cluster, suburb - dens: >300, totalpop: >5000, within 3km of 23 or 22
            (13) Rural, village  - dens: >300, totalpop: >500, <5000
            (12) Rural, dispersed, low density - dens: >50,
            (11) Rural, dispersed, low density - the rest that are populated
        
        :param urbDens: integer of the minimum density value to be counted as urban
        :param hdDens: integer of the minimum density value to be counted as high density
        :param urbThresh: integer minimum total settlement population to be considered urban
        :param hdThresh: integer minimum total settlement population to be considered high density        
        '''
        
        popRaster = self.inR
        data = popRaster.read()
        urban_raster = data * 0
        final_raster = data[0,:,:] * 0 + 11
        
        urban_raster[np.where(data > hdDens)] = 30
        idx = 0
        urban_raster = urban_raster.astype("int16")
        allFeatures = []
        
        if verbose:
            tPrint(f'{print_message}: Smoothing Urban Clusters')
        # Smooth the HD urban clusters
        def modal(P):
            mode = stats.mode(P)
            return(mode.mode[0])

        smooth_urban = generic_filter(urban_raster[0,:,:], modal, (3,3))
        yy = np.dstack([smooth_urban, urban_raster[0,:,:]])
        urban_raster[0,:,:] = np.amax(yy, axis=2)        
        
        #Analyze the high density shapes
        if verbose:
            tPrint(f'{print_message}: extracting HD clusters')
        
        for cShape, value in features.shapes(urban_raster, transform=popRaster.transform):
            if idx % 1000 == 0 and verbose:
                tPrint("%s: Creating Shape %s" % (print_message, idx))
            idx = idx + 1
            if value > 0:
                # RRemove holes from urban shape
                origShape = cShape
                xx = shape(cShape)
                xx = Polygon(xx.exterior)
                cShape = xx.__geo_interface__
                #If the shape is urban, claculate total pop        
                mask = rasterize([(cShape, 0)], out_shape=data[0,:,:].shape,fill=1,transform=popRaster.transform)
                inData = np.ma.array(data=data, mask=mask.astype(bool))
                pop = np.nansum(inData) 

                val = 0
                if pop > urbThresh:
                    ### TODO - if the totalpop is < 50k, may need to unsmooth the shape
                    val = 23
                if pop > hdThresh:
                    val = 30
                
                #Burn value into the final raster
                mask = (mask^1) * val        
                yy = np.dstack([final_raster, mask])
                final_raster = np.amax(yy, axis=2)
                allFeatures.append([idx, pop, val, shape(geojson.loads(json.dumps(cShape)))])
        
        HD_raster = final_raster
            
        urban_raster = data * 0
        final_raster = data[0,:,:] * 0 + 11    
        urban_raster[np.where(data > urbDens)] = 22
        urban_raster = urban_raster.astype("int16")
        #Analyze the high density shapes
        if verbose:
            tPrint(f'{print_message}: extracting URBAN clusters')
        
        for cShape, value in features.shapes(urban_raster, transform=popRaster.transform, connectivity=8):
            if idx % 1000 == 0 and verbose:
                tPrint("%s: Creating Shape %s" % (print_message, idx))
            idx = idx + 1
            if value > 0:
                #If the shape is urban, claculate total pop        
                mask = rasterize([(cShape, 0)], out_shape=data[0,:,:].shape,fill=1,transform=popRaster.transform)
                inData = np.ma.array(data=data, mask=mask.astype(bool))
                pop = np.nansum(inData) 
                val = 0
                if pop > 500:
                    val = 13                
                if pop > urbThresh:
                    val = 21
                #Burn value into the final raster
                mask = (mask^1) * val        
                yy = np.dstack([final_raster, mask])
                final_raster = np.amax(yy, axis=2)
                allFeatures.append([idx, pop, val, shape(geojson.loads(json.dumps(cShape)))])
        URB_raster = final_raster
   
        #Combine the urban layers
        yy = np.dstack([HD_raster, URB_raster])
        final_raster = np.amax(yy, axis=2)
        final_raster[(final_raster == 11) & (data[0,:,:] > minPopThresh) & (data[0,:,:] < urbDens)] = 12
        
        if verbose:
            tPrint(f'{print_message}: performing distance calculations')
        
        #Identify the urban areas of class 22 by measuring distance to other features
        feats = allFeatures
        sel = pd.DataFrame(feats, columns=['ID','POP','CLASS','geometry'])
        sel = gpd.GeoDataFrame(sel, geometry="geometry", crs=self.inR.crs)
        to_be    = sel.loc[sel['CLASS'] == 21]
        to_be    = to_be.loc[to_be['POP'] < hdThresh]        
        distance = sel.loc[sel['CLASS'].isin([21,23])]
        dist_shp = distance.sindex        
        
        def calc_nearest(x, dist_gpd, dist_idx):
            xx = dist_gpd.iloc[list(dist_idx.nearest([x.centroid.x, x.centroid.y], 2))]
            dists = xx['geometry'].apply(lambda y: y.distance(x))
            try:
                return(min(dists[dists > 0]))
            except:
                return(0)
            
            return(max(dists))           
        to_be['dist'] = to_be['geometry'].apply(lambda x: calc_nearest(x, distance, dist_shp))
        features_22 = to_be.loc[to_be['dist'] > 3000]
        
        #Burn features into output raster
        cShape = features_22.unary_union.__geo_interface__
        mask = rasterize([(cShape, 0)], out_shape=data[0,:,:].shape,fill=1,transform=popRaster.transform)
        mask_vals = (mask^1) * 22
        
        final_raster = (final_raster * mask) + mask_vals
        
        if len(out_raster) > 0:
            out_metadata = popRaster.meta.copy()
            out_metadata['dtype'] = urban_raster.dtype
            out_metadata['nodata'] = -999
            final_raster = final_raster.astype(out_metadata['dtype'])
            with rasterio.open(out_raster, 'w', **out_metadata) as rOut:
                rOut.write_band(1, final_raster)
                
        return({'raster':final_raster, 'shapes':allFeatures, 'HD':HD_raster, 'URB':URB_raster})
            
            
    
    def calculateUrban(self, densVal=300, totalPopThresh=5000, smooth=False, verbose=False, queen=False,
                        raster='', raster_pop='', print_message=''):
        '''
        Generate urban extents from gridded population data through the application of a minimum
            density threshold and a minimum total population threshold
            
        :param densVal: integer of the minimum density value to be counted as urban
        :param totalPopThresh: integer minimum total settlement population to ne considered urban
        :param smooth: boolean to run a single modal smoothing function (this should be run when running 
                        on WorldPop as the increased resolution often leads to small holes and funny shapes
        :param verbose: boolean on what messages to receive
        :param queen: boolean to determine whether to dissolve final shape to connect queen's contiguity
        :param raster: string path to create a boolean raster of urban and not. 
                        Empty string is the default and will create no raster
        :param raster_pop: string path to create a raster of the population layer only in the urban areas
                            Empty string is the default and will create no raster
        :returns: GeoPandasDataFrame of the urban extents
        '''

        popRaster = self.inR
        data = popRaster.read()
        urbanData = (data > densVal) * 1
        urbanData = urbanData.astype('int16')
            
        if verbose:
            tPrint("%s: Read in urban data" % print_message)

        idx = 0     
        # create output array to store urban raster
        urban_raster = urbanData * 0
        for cShape, value in features.shapes(urbanData, transform=popRaster.transform):
            if idx % 1000 == 0 and verbose:
                tPrint("%s: Creating Shape %s" % (print_message, idx))
            if value == 1:            
                #If the shape is urban, claculate total pop        
                mask = rasterize([(cShape, 0)], out_shape=data[0,:,:].shape,fill=1,transform=popRaster.transform)
                inData = np.ma.array(data=data, mask=mask.astype(bool))
                curPop = np.nansum(inData) 
                if curPop < 0: # when smoothed, sometimes the pop withh be < 0 because of no data
                    inData = np.ma.array(data=inData, mask=(inData < 0).astype(bool))
                    curPop = np.nansum(inData) 
                if curPop > totalPopThresh:            
                    urban_raster += (mask^1)
                
            idx = idx + 1
        
        if smooth:
            inD = urban_raster[0,:,:]
            total_urban_cells = inD.sum()
            current_cells = 0
            cnt = 0
            urban_res = inD
            while (total_urban_cells != current_cells) and (cnt < 100):
                cnt = cnt + 1
                total_urban_cells = current_cells
                newD = ndimage.median_filter(urban_res, size=3)
                stackD = np.dstack([newD, inD])
                finalD = np.amax(stackD, axis=2)
                current_cells = finalD.sum()
                urban_res = finalD
            urban_raster[0,:,:] = urban_res
        
        allFeatures = []
        badFeatures = []
        for cShape, value in features.shapes(urban_raster, transform=popRaster.transform):
            if idx % 1000 == 0 and verbose:
                tPrint("%s: Creating Shape %s" % (print_message, idx))
            if value == 1:            
                #If the shape is urban, claculate total pop        
                mask = rasterize([(cShape, 0)], out_shape=data[0,:,:].shape,fill=1,transform=popRaster.transform)
                inData = np.ma.array(data=data, mask=mask.astype(bool))
                curPop = np.nansum(inData) 
                if curPop < 0: # when smoothed, sometimes the pop withh be < 0 because of no data
                    inData = np.ma.array(data=inData, mask=(inData < 0).astype(bool))
                    curPop = np.nansum(inData) 
                if curPop > totalPopThresh:            
                    allFeatures.append([idx, curPop, shape(geojson.loads(json.dumps(cShape)))])

            idx = idx + 1
        
        if len(raster):
            out_metadata = popRaster.meta.copy()
            out_metadata['dtype'] = urban_raster.dtype
            out_metadata['nodata'] = 0
            with rasterio.open(raster, 'w', **out_metadata) as rOut:
                rOut.write(urban_raster)
        
        if len(raster_pop):
            out_metadata = popRaster.meta.copy()
            urban_pop = data * urban_raster
            with rasterio.open(raster_pop, 'w', **out_metadata) as rOut:
                rOut.write(urban_pop)
        
        xx = pd.DataFrame(allFeatures, columns=['ID', 'Pop','geometry'])
        xxGeom = gpd.GeoDataFrame(xx, geometry='geometry')
        xxGeom.crs = popRaster.crs
        
        if queen:
            xxGeom['geometry '] = xxGeom.buffer((popRaster.res[0] / 2))
            s = xxGeom['geometry']
            overlap_matrix = s.apply(lambda x: s.intersects(x)).values.astype(int)
            n, ids = connected_components(overlap_matrix)
            xxGeom['group'] = ids
            xxGeom = xxGeom.dissolve(by="group", aggfunc="sum")
        
        return(xxGeom)
                
        