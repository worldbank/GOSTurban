"""Integrative tests for UrbanRaster.py based on the tutorial notebook."""
import os
import rasterio
import geopandas as gpd
import GOSTurban.UrbanRaster as urban


def test_urbanraster_integrated():
    # Define input population raster
    tutorial_folder = "./data/tutorial_data"
    pop_file = os.path.join(tutorial_folder, "wp_2020_1k_AOI.tif")

    inR = rasterio.open(pop_file)
    # Initiate the urban calculator
    urban_calculator = urban.urbanGriddedPop(inR)

    # Extract the urban extents
    # (minimum density 300/km2, minimum total population 5000)
    urban_extents = urban_calculator.calculateUrban(
        densVal=300, totalPopThresh=5000, smooth=False, queen=False, verbose=True
    )
    urban_extents["Type"] = 1
    urban_extents.head()

    # assert that urban_extents is a geopandas.GeoDataFrame
    assert isinstance(urban_extents, gpd.GeoDataFrame)

    # Extract the high density urban extents
    # (minimum density 1500/km2, minimum total population 50000)
    hd_urban_extents = urban_calculator.calculateUrban(
        densVal=1500,
        totalPopThresh=50000,
        smooth=True,
        queen=True,  # high density extents use queen's case contiguity, and
        verbose=True,
    )  # High density extents have hole smoothing applied.
    hd_urban_extents["Type"] = 2
    hd_urban_extents.head()

    # assert that hd_urban_extents is a geopandas.GeoDataFrame
    assert isinstance(hd_urban_extents, gpd.GeoDataFrame)
