import sys, os
import rasterio

import geopandas as gpd
import GOST_Urban.UrbanRaster as urban
from GOSTRocks.misc import tPrint

def main_demo():
    """ Generate the urban extents for a given population raster
    """
    data_folder = os.path.abspath("../../Data/tutorial_data")    
    pop_file = os.path.join(data_folder, "wp_2020_1k_AOI.tif")
    out_urban = os.path.join(data_folder, "urban_extents.geojson")
    out_hd_urban = os.path.join(data_folder, "hd_urban_extents.geojson")

    tPrint(f"Running demo urbanization calculation for {pop_file}")

    inR = rasterio.open(pop_file)
    urban_calculator = urban.urbanGriddedPop(inR)
    urban_extents = urban_calculator.calculateUrban(densVal=300, totalPopThresh=5000, 
                                               smooth=False, queen=False,
                                               verbose=True)
    hd_urban_extents = urban_calculator.calculateUrban(densVal=1500, totalPopThresh=50000, 
                                               smooth=True, queen=True,
                                               verbose=True) 

    urban_extents.to_file(out_urban, driver="GeoJSON")
    hd_urban_extents.to_file(out_hd_urban, driver="GeoJSON")

    # Map results
    out_map = os.path.join(data_folder, "urban_extents.png")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run demo urbanization method')
    parser.add_argument('--demo', action='store_true', help='Run the demo urbanization calculation')


    args = parser.parse_args()
    main_demo()