import sys
import os
import rasterio
import rasterio.warp

import pandas as pd
import geopandas as gpd


# Import raster helpers
import GOSTRocks.rasterMisc as rMisc
import GOSTRocks.ntlMisc as ntl
from GOSTRocks.misc import tPrint

# Import GOST urban functions
sys.path.append("../../../src")
import GOST_Urban.UrbanRaster as urban


class urban_country:
    """helper function to centralize urban calculations for a single country"""

    def __init__(self, iso3, sel_country, cur_folder, inP):
        """calculate urban extents for selected country and population raster

        INPUT
            iso3 [string] - ISO 3 of selected country
            sel_country [geopandas dataframe] - selected country bounds
            cur_folder [string path] - path to output folder
            inP [rasterio read] - opened population raster dataset
        """
        self.iso3 = iso3
        self.sel_country = sel_country
        self.cur_folder = cur_folder
        self.urban_extents_file = os.path.join(
            cur_folder, f"{iso3}_urban_extents.geojson"
        )
        self.urban_extents_raster_file = os.path.join(
            cur_folder, f"{iso3}_urban_extents.tif"
        )
        self.urban_extents_hd_file = os.path.join(
            cur_folder, f"{iso3}_urban_extents_hd.geojson"
        )
        self.urban_extents_hd_raster_file = os.path.join(
            cur_folder, f"{iso3}_urban_extents_hd.tif"
        )

        self.ghsl_folder = os.path.join(self.cur_folder, "GHSL_Rasters")

        # Define zonal summary files
        self.urban_ntl = os.path.join(cur_folder, f"{iso3}_urban_ntl.csv")
        self.urban_hd_ntl = os.path.join(cur_folder, f"{iso3}_hd_urban_ntl.csv")

        self.urban_ghsl = os.path.join(cur_folder, f"{iso3}_urban_ghsl.csv")
        self.urban_hd_ghsl = os.path.join(cur_folder, f"{iso3}_urban_hd_ghsl.csv")

        if type(inP) == str:
            inP = rasterio.open(inP)
        self.inP = inP

    def calculate_urban_extents(self, calculate_area=True, area_crs=3857):
        """Run EC urban extent analysis"""
        urban_calculator = urban.urbanGriddedPop(self.inP)
        if not os.path.exists(self.urban_extents_file):
            tPrint(f"Running urbanization for {self.iso3}")
            urban_extents = urban_calculator.calculateUrban(
                densVal=300,
                totalPopThresh=5000,
                smooth=False,
                queen=False,
                verbose=True,
                raster=self.urban_extents_raster_file,
            )
            # Calculate area of urban extents
            if calculate_area:
                urban_extents = urban_extents.to_crs(area_crs)
                urban_extents = urban_extents.to_crs(area_crs)
                urban_extents["area_km"] = urban_extents["geometry"].apply(
                    lambda x: x.area / 1000000
                )

            # Name urban extents
            if urban_extents.crs.to_epsg() != 4326:
                urban_extents = urban_extents.to_crs(4326)
                try:
                    urban_extents = urban.geocode_cities(urban_extents)
                except:
                    pass

            urban_extents.to_file(self.urban_extents_file, driver="GeoJSON")
            self.urban_extents = urban_extents
        else:
            self.urban_extents = gpd.read_file(self.urban_extents_file)

        if not os.path.exists(self.urban_extents_hd_file):
            urban_extents_hd = urban_calculator.calculateUrban(
                densVal=1500,
                totalPopThresh=50000,
                smooth=True,
                queen=False,
                verbose=True,
                raster=self.urban_extents_hd_raster_file,
            )
            # Calculate area of urban extents
            if calculate_area:
                urban_extents_hd = urban_extents_hd.to_crs(area_crs)
                urban_extents_hd = urban_extents_hd.to_crs(area_crs)
                urban_extents_hd["area_km"] = urban_extents_hd["geometry"].apply(
                    lambda x: x.area / 1000000
                )

            # Name urban extents
            if urban_extents_hd.crs.to_epsg() != 4326:
                urban_extents_hd = urban_extents_hd.to_crs(4326)
                try:
                    urban_extents_hd = urban.geocode_cities(urban_extents_hd)
                except:
                    pass
            urban_extents_hd.to_file(self.urban_extents_hd_file, driver="GeoJSON")
            self.urban_extents_hd = urban_extents_hd
        else:
            self.urban_extents_hd = gpd.read_file(self.urban_extents_hd_file)

    def summarize_ntl(self, ntl_files=[]):
        """run zonal analysis on nighttime lights using urban extents"""
        if (not os.path.exists(self.urban_ntl)) or (
            not os.path.exists(self.urban_hd_ntl)
        ):
            if len(ntl_files) == 0:
                ntl_files = ntl.aws_search_ntl()
            for ntl_file in ntl_files:
                name = ntl_file.split("/")[-1].split("_")[2][:8]
                try:
                    inR = rasterio.open(ntl_file)
                    # tPrint("Processing %s" % name)
                    viirs_folder = os.path.join(self.cur_folder, "VIIRS")
                    urban_res_file = os.path.join(viirs_folder, f"URBAN_{name}.csv")
                    urban_hd_res_file = os.path.join(
                        viirs_folder, f"HD_URBAN_{name}.csv"
                    )

                    if not os.path.exists(viirs_folder):
                        os.makedirs(viirs_folder)

                    try:
                        urbanD = self.urban_extents
                        urbanHD = self.urban_extents_hd
                    except:
                        self.calculate_urban_extents()
                        urbanD = self.urban_extents
                        urbanHD = self.urban_extents_hd

                    # Urban Summary
                    if not os.path.exists(urban_res_file):
                        urban_res = rMisc.zonalStats(urbanD, inR, minVal=0.1)
                        col_names = [
                            f"URBAN_{name}_{x}" for x in ["SUM", "MIN", "MAX", "MEAN"]
                        ]
                        urban_df = pd.DataFrame(urban_res, columns=col_names)
                        urban_df.to_csv(urban_res_file)
                    # HD Urban Summary
                    if not os.path.exists(urban_hd_res_file):
                        hd_urban_res = rMisc.zonalStats(urbanHD, inR, minVal=0.1)
                        col_names = [
                            f"HD_URBAN_{name}_{x}"
                            for x in ["SUM", "MIN", "MAX", "MEAN"]
                        ]
                        hd_urban_df = pd.DataFrame(hd_urban_res, columns=col_names)
                        hd_urban_df.to_csv(urban_hd_res_file)
                except:
                    tPrint(f"***********ERROR with {iso3} and {name}")

            # Compile VIIRS results
            urb_files = [x for x in os.listdir(viirs_folder) if x.startswith("URBAN")]
            for x in urb_files:
                tempD = pd.read_csv(os.path.join(viirs_folder, x), index_col=0)
                urbanD[x[:-4]] = tempD.iloc[:, 0]

            hd_urb_files = [
                x for x in os.listdir(viirs_folder) if x.startswith("HD_URBAN")
            ]
            for x in hd_urb_files:
                tempD = pd.read_csv(os.path.join(viirs_folder, x), index_col=0)
                urbanHD[x[:-4]] = tempD.iloc[:, 0]

            urbanD.drop(["geometry"], axis=1).to_csv(self.urban_ntl)
            urbanHD.drop(["geometry"], axis=1).to_csv(self.urban_hd_ntl)

    def summarize_ghsl(
        self, ghsl_files, binary_calc=False, binary_thresh=1000, clip_raster=False
    ):
        """Summarize GHSL data

        INPUT
            ghsl_files [list of paths] - path to individual built area raster files
            [optional] binary_calc [binary, default=False] - if True, additionally calculate zonal stats on a binary built raster
            [optional] binary_thresh [int, default=1000] - if binary_calc is True, all cells above threshold will be considered built
            [optional] clip_raster [binary, default=False] - if True, clip the GHSL datasets for the calculations
        """
        if (not os.path.exists(self.urban_ghsl)) or (
            not os.path.exists(self.urban_hd_ghsl)
        ):
            try:
                urbanD = self.urban_extents
                urbanHD = self.urban_extents_hd
            except:
                self.calculate_urban_extents()
                urbanD = self.urban_extents
                urbanHD = self.urban_extents_hd

            for ghsl_file in ghsl_files:
                date = os.path.basename(ghsl_file).split("_")[3]
                tPrint(date)
                inR = rasterio.open(ghsl_file)
                if urbanD.crs != inR.crs:
                    urbanD = urbanD.to_crs(inR.crs)
                    urbanHD = urbanHD.to_crs(inR.crs)

                local_file = os.path.join(self.ghsl_folder, os.path.basename(ghsl_file))
                if clip_raster:
                    if not os.path.exists(self.ghsl_folder):
                        os.makedirs(self.ghsl_folder)
                    if not os.path.exists(local_file):
                        rMisc.clipRaster(inR, self.sel_country, local_file)

                res_urban = rMisc.zonalStats(urbanD, inR, minVal=0)
                res_urban = pd.DataFrame(
                    res_urban, columns=["SUM", "MIN", "MAX", "MEAN"]
                )
                urbanD[f"ghsl_{date}"] = res_urban["SUM"]

                res_hd_urban = rMisc.zonalStats(urbanHD, inR, minVal=0)
                res_hd_urban = pd.DataFrame(
                    res_hd_urban, columns=["SUM", "MIN", "MAX", "MEAN"]
                )
                urbanHD[f"ghsl_{date}"] = res_hd_urban["SUM"]

                if binary_calc:  # run zonal stats on a binary built layer
                    try:
                        localR = rasterio.open(local_file)
                        inD = localR.read()
                        inD[inD == localR.meta["nodata"]] = 0
                    except:
                        raise (
                            ValueError(
                                "In order to calculate binary zonal, you need to clip out local ghsl data"
                            )
                        )
                    inD = inD > binary_thresh
                    with rMisc.create_rasterio_inmemory(localR.profile, inD) as binaryR:
                        res_urban = rMisc.zonalStats(urbanD, binaryR, minVal=0)
                        res_urban = pd.DataFrame(
                            res_urban, columns=["SUM", "MIN", "MAX", "MEAN"]
                        )
                        urbanD[f"ghsl_binary_{date}"] = res_urban["SUM"]

                        res_hd_urban = rMisc.zonalStats(urbanHD, binaryR, minVal=0)
                        res_hd_urban = pd.DataFrame(
                            res_hd_urban, columns=["SUM", "MIN", "MAX", "MEAN"]
                        )
                        urbanHD[f"ghsl_binary_{date}"] = res_hd_urban["SUM"]

            # Write results to file
            pd.DataFrame(urbanD.drop(["geometry"], axis=1)).to_csv(self.urban_ghsl)
            pd.DataFrame(urbanHD.drop(["geometry"], axis=1)).to_csv(self.urban_hd_ghsl)

    def delete_urban_data(self):
        """delete urban extents"""
        for cFile in [
            self.urban_extents_file,
            self.urban_extents_raster_file,
            self.urban_extents_hd_file,
            self.urban_extents_hd_raster_file,
        ]:
            try:
                os.remove(cFile)
            except:
                pass
