import sys, os, importlib, shutil
import requests
import rasterio, elevation, richdem
import rasterio.warp
from rasterio import features

import pandas as pd
import geopandas as gpd
import numpy as np

sys.path.append("../")
import src.UrbanRaster as urban

#Import raster helpers
sys.path.append("../../gostrocks/src")

import GOSTRocks.rasterMisc as rMisc
from GOSTRocks.misc import tPrint

class summarize_population(object):
    ''' summarize population and urban populations for defined admin regions
    '''
    def __init__(self, pop_layer, admin_layer, temp_folder=''):
        self.pop_layer = pop_layer
        self.urban_layer = pop_layer.replace(".tif", "_urban.tif")
        self.urban_hd_layer = pop_layer.replace(".tif", "_urban_hd.tif")
        self.admin_layer = admin_layer
        
        #Open population layer
        self.in_pop = rasterio.open(self.pop_layer)
        if self.admin_layer.crs != self.in_pop.crs:
            self.admin_layer = self.admin_layer.to_crs(self.in_pop.crs)
        
        if temp_folder == '':
            self.temp_folder = os.path.dirname(self.pop_layer)
        else:
            self.temp_folder = temp_folder
        
    def check_inputs(self):
        ''' Ensure all layers exist
        '''
        check_vals = {}
        good = True
        for lyr in [self.pop_layer, self.urban_layer, self.urban_hd_layer]:
            check_vals[lyr] = os.path.exists(lyr)
            if not check_vals[lyr]:
                good = False
        self.check_vals = check_vals
        return(good)
    
    def calculate_zonal(self, out_name=''):
        
        inP = self.in_pop.read()
        inA = self.admin_layer #gpd.read_file(self.admin_layer)        
        
        res = rMisc.zonalStats(inA, self.in_pop, minVal=0)
        final = pd.DataFrame(res, columns=["TOTALPOP_%s_%s" % (os.path.basename(self.pop_layer), x) for x in ['SUM', 'MIN', 'MAX', 'MEAN']])
            
        for lyr in [self.urban_layer, self.urban_hd_layer]:
            name = os.path.basename(lyr)
            in_urban = rasterio.open(lyr)
            inU = in_urban.read()
            cur_pop = inP * inU
            out_file = os.path.join(self.temp_folder, "urban_pop.tif")
            
            with rasterio.open(out_file, 'w', **self.in_pop.meta) as out_urban:
                out_urban.write(cur_pop)
                
            res = rMisc.zonalStats(inA, out_file, minVal=0)
            res = pd.DataFrame(res, columns=["%s_%s_%s" % (out_name, name, x) for x in ['SUM', 'MIN', 'MAX', 'MEAN']])
            try:
                final = final.join(res)
            except:
                final = res
        return(final)

class urban_country(object):
    '''
    '''
    
    def __init__(self, iso3, output_folder, country_bounds):
        ''' Create object for managing input data for summarizing urban extents
        
        INPUT
        :param: iso3 - string describing iso3 code
        :param: output_folder - string path to folder to hold results
        :param: country_bounds - geopandas dataframe of admin0 boundary
        
        '''
        self.iso3 = iso3
        self.out_folder = output_folder
        self.final_folder = os.path.join(self.out_folder, "FINAL_STANDARD")
        if not os.path.exists(self.out_folder):
            os.makedirs(self.out_folder)
            os.makedirs(self.final_folder)
            
        self.dem_file = os.path.join(output_folder, "%s_DEM.tif" % iso3)
        self.slope_file = os.path.join(output_folder, "%s_SLOPE.tif" % iso3)
        self.lc_file = os.path.join(output_folder, "%s_LC.tif" % iso3)
        self.lc_file_h20 = os.path.join(output_folder, "%s_LC_H20.tif" % iso3)
        self.ghspop_file = os.path.join(output_folder, "%s_GHS.tif" % iso3)
        self.ghsbuilt_file = os.path.join(output_folder, "%s_GHSBUILT.tif" % iso3)
        self.admin_file  =  os.path.join(output_folder, "%s_ADMIN.tif" % iso3)
        self.admin_shp  =  os.path.join(self.final_folder, "%s_ADMIN.shp" % iso3)
        
        self.inD = country_bounds
        # Write shapefile to file
        if not os.path.exists(self.admin_shp):
            self.inD.to_file(self.admin_shp)
            
    def process_dem(self):
        ''' Download DEM from AWS, calculate slope
        '''
        # Download DEM

        if not os.path.exists(self.dem_file):
            tPrint("Downloading DEM")
            elevation.clip(bounds=self.inD.total_bounds, max_download_tiles=90000, output=self.dem_file, product='SRTM3')

        # Calculate slope
        if not os.path.exists(self.slope_file) and os.path.exists(self.dem_file):
            tPrint("Calculating slope")
            in_dem = rasterio.open(self.dem_file)
            in_dem_data = in_dem.read()
            beau  = richdem.rdarray(in_dem_data[0,:,:], no_data=in_dem.meta['nodata'])
            slope = richdem.TerrainAttribute(beau, attrib='slope_riserun')
            meta = in_dem.meta.copy()
            meta.update(dtype = slope.dtype)
            with rasterio.open(self.slope_file, 'w', **meta) as outR:
                outR.write_band(1, slope)
                
    def extract_layers(self, global_landcover, global_ghspop, global_ghbuilt):
        ''' extract global layers for current country
        '''
        # Extract water from globcover
        if not os.path.exists(self.lc_file_h20):
            tPrint("Extracting water")
            if not os.path.exists(self.lc_file):
                rMisc.clipRaster(rasterio.open(global_landcover), self.inD, self.lc_file)
            in_lc = rasterio.open(self.lc_file)
            inL = in_lc.read()
            lcmeta = in_lc.meta.copy()
            tempL = (inL == 210).astype(lcmeta['dtype'])
            lcmeta.update(nodata=255)
            with rasterio.open(self.lc_file_h20, 'w', **lcmeta) as out:
                out.write(tempL)
            os.remove(self.lc_file)
            
        #Extract GHS-Pop
        if not os.path.exists(self.ghspop_file):
            tPrint("Extracting GHS-POP")
            rMisc.clipRaster(rasterio.open(global_ghspop), self.inD, self.ghspop_file)

        #Extract GHS-Built
        if not os.path.exists(self.ghsbuilt_file):
            tPrint("Clipping GHS-Built")
            rMisc.clipRaster(rasterio.open(global_ghbuilt), self.inD, self.ghsbuilt_file)
            
        #Rasterize admin boundaries
        if not os.path.exists(self.admin_file):
            tPrint("Rasterizing admin boundaries")
            xx = rasterio.open(self.ghspop_file)
            res = xx.meta['transform'][0]
            tempD = self.inD.to_crs(xx.crs)
            shapes = ((row['geometry'], 1) for idx, row in tempD.iterrows())
            burned = features.rasterize(shapes=shapes, out_shape=xx.shape, fill=0, transform=xx.meta['transform'], dtype='int16')
            meta = xx.meta.copy()
            meta.update(dtype=burned.dtype)
            with rasterio.open(self.admin_file, 'w', **meta) as outR:
                outR.write_band(1, burned)
                
    def calculate_urban(self, pop_files):
        ''' Calculate urban and HD urban extents from population files
        '''
        # Calculate urban extents from population layers
        tPrint("***Starting ")
        ghs_R = rasterio.open(self.ghspop_file)
        for p_file in pop_files:
            final_pop = os.path.join(self.final_folder, os.path.basename(p_file))
            final_urban    = final_pop.replace(".tif", "_urban.tif")
            final_urban_hd = final_pop.replace(".tif", "_urban_hd.tif")
            urbanR = urban.urbanGriddedPop(final_pop)
            #calculate density values
            in_raster = rasterio.open(p_file)
            width_ratio = in_raster.shape[0] / ghs_R.shape[0]
            height_ratio = in_raster.shape[1] / ghs_R.shape[1]
            total_ratio = width_ratio * height_ratio
            tPrint(final_urban)
            if not os.path.exists(final_urban):
                urban_shp   = urbanR.calculateUrban(densVal= (3 * total_ratio), totalPopThresh=5000,  raster=final_urban)
            if not os.path.exists(final_urban_hd):
                cluster_shp = urbanR.calculateUrban(densVal=(15 * total_ratio), totalPopThresh=50000, raster=final_urban_hd)
            tPrint(final_urban_hd)
    

    def pop_zonal_admin(self, admin_layer):
        ''' calculate urban and rural 
        
            :param: - admin_layer
        '''
        for pop_file in self.final_pop_files:
            yy = summarize_population(pop_file, admin_layer)
            if yy.check_inputs():
                res = yy.calculate_zonal(out_name='')
                try:
                    final = final.join(res)
                except:
                    final = res
        admin_layer = admin_layer.reset_index()
        final = final.filter(regex='_SUM')
        final = final.join(admin_layer)
        final = final.drop(['geometry'], axis=1)
        return(final)       
        
    
    def standardize_rasters(self, pop_files):
        '''
        
            :param: pop_files - list of string paths to population layers
        '''
        ghs_R = rasterio.open(self.ghspop_file)    
        out_array = ghs_R.read() * 0
        #Read in admin data and get nodata area
        in_admin = rasterio.open(self.admin_file)
        in_a = in_admin.read()
        in_a_mask = in_a == 0
        
        file_defs = [
                #file, type, scale values
                [self.admin_file,'C',False],
                [self.ghspop_file, 'N', True],
                [self.lc_file_h20, 'C', False],
                [self.slope_file, 'N', False],
                [self.dem_file, 'N', False],
                [self.ghsbuilt_file, 'N', False]        
            ]
            
        self.final_pop_files = [os.path.join(self.final_folder, os.path.basename(self.ghspop_file))]
        for cFile in pop_files:            
            self.final_pop_files.append(os.path.join(self.final_folder, os.path.basename(cFile)))
            file_defs.append([cFile, 'N', True])
                
        for file_def in file_defs:
            print(file_def[0])
            out_file = os.path.join(self.final_folder, os.path.basename(file_def[0]))    
            # scale and project file to GHS pop
            if not os.path.exists(out_file) and os.path.exists(file_def[0]):
                out_array = ghs_R.read() * 0
                in_raster = rasterio.open(file_def[0])
                in_r = in_raster.read()
                rSample = rasterio.warp.Resampling.cubic
                if file_def[1] == 'C':
                    rSample = rasterio.warp.Resampling.nearest
                rasterio.warp.reproject(in_r, out_array, 
                                        src_transform=in_raster.meta['transform'], dst_transform=ghs_R.meta['transform'],
                                        src_crs = in_raster.crs, dst_crs = ghs_R.crs,
                                        src_nodata = in_raster.meta['nodata'], dst_nodata = ghs_R.meta['nodata'],
                                       resample = rSample)
                out_array[out_array == ghs_R.meta['nodata']] = 0.
                # If values are to be scaled based on area change, do it here
                if file_def[2]:
                    #Determine scale difference between rasters
                    width_ratio = in_raster.shape[0] / ghs_R.shape[0]
                    height_ratio = in_raster.shape[1] / ghs_R.shape[1]
                    total_ratio = width_ratio * height_ratio
                    out_array = out_array * total_ratio
                    out_array[out_array < 0] = ghs_R.meta['nodata']
                # Set area outside national boundaries to nodata
                out_array[in_a_mask] = ghs_R.meta['nodata']
                out_meta = ghs_R.meta.copy()
                out_meta.update(nodata=ghs_R.meta['nodata'])
                with rasterio.open(out_file, 'w', **out_meta) as outR:
                    outR.write(out_array)
            # Write no data layers to file
            out_no_data_file = os.path.join(self.final_folder, "NO_DATA_%s" % os.path.basename(file_def[0]))
            if not os.path.exists(out_no_data_file) and os.path.exists(file_def[0]):
                out_array = ghs_R.read() * 0
                in_raster = rasterio.open(file_def[0])
                in_r = in_raster.read()
                # create binary file defining no data area
                in_r = (in_r == in_raster.meta['nodata']).astype(ghs_R.meta['dtype'])
                rasterio.warp.reproject(in_r, out_array, 
                                        src_transform=in_raster.meta['transform'], dst_transform=ghs_R.meta['transform'],
                                        src_crs = in_raster.crs, dst_crs = ghs_R.crs,
                                        src_nodata = in_raster.meta['nodata'], dst_nodata = ghs_R.meta['nodata'],
                                        resample = rasterio.warp.Resampling.nearest)
                out_meta = ghs_R.meta.copy()
                with rasterio.open(out_no_data_file, 'w', **out_meta) as outR:
                    outR.write(out_array)
                
        
                
    
    
    
    
    
    
    
    
    
    
    
    
    
            