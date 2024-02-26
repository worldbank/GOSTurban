import sys
import os
import rasterio
import elevation
import richdem
import rasterio.warp

from rasterio import features

import pandas as pd
import numpy as np

sys.path.append("../")
import GOST_Urban.UrbanRaster as urban

import GOSTRocks.rasterMisc as rMisc
from GOSTRocks.misc import tPrint


class summarize_population(object):
    """summarize population and urban populations for defined admin regions"""

    def __init__(
        self, pop_layer, admin_layer, urban_layer="", hd_urban_layer="", temp_folder=""
    ):
        """Summarize population into urban and rural based on GOST_Urban.UrbanRaster.calculateUrban

        INPUT
        pop_layer [string] - path
        """
        self.pop_layer = pop_layer

        self.urban_layer = urban_layer
        if self.urban_layer == "":
            self.urban_layer = pop_layer.replace(".tif", "_urban.tif")

        self.urban_hd_layer = hd_urban_layer
        if self.urban_hd_layer == "":
            self.urban_hd_layer = pop_layer.replace(".tif", "_urban_hd.tif")
        self.admin_layer = admin_layer

        # Open population layer
        self.in_pop = rasterio.open(self.pop_layer)
        if self.admin_layer.crs != self.in_pop.crs:
            self.admin_layer = self.admin_layer.to_crs(self.in_pop.crs)

        if temp_folder == "":
            self.temp_folder = os.path.dirname(self.pop_layer)
        else:
            self.temp_folder = temp_folder

    def check_inputs(self):
        """Ensure all layers exist"""
        check_vals = {}
        good = True
        for lyr in [self.pop_layer, self.urban_layer, self.urban_hd_layer]:
            check_vals[lyr] = os.path.exists(lyr)
            if not check_vals[lyr]:
                good = False
        self.check_vals = check_vals
        return good

    def calculate_zonal(self, out_name="", convert_urban_binary=False):
        """Run zonal statistics on input admin layers, population layers, and urban layers

        Args:
            out_name (str, optional): name to append to output populations columns. Defaults to ''.
            convert_urban_binary (bool, optional): option to convert urban layer to binary. Anything > 0 becomes binary 1 for urban. Defaults to False.
        """

        inP = self.in_pop.read()
        inA = self.admin_layer  # gpd.read_file(self.admin_layer)

        res = rMisc.zonalStats(inA, self.in_pop, minVal=0)
        final = pd.DataFrame(
            res,
            columns=[
                "TOTALPOP_%s_%s"
                % (os.path.basename(self.pop_layer).replace(".tif", ""), x)
                for x in ["SUM", "MIN", "MAX", "MEAN"]
            ],
        )

        for lyr in [self.urban_layer, self.urban_hd_layer]:
            name = os.path.basename(lyr).replace(".tif", "")
            in_urban = rasterio.open(lyr)
            inU = in_urban.read()
            if convert_urban_binary:
                inU = (inU > 0) * 1
            cur_pop = inP * inU
            out_file = os.path.join(self.temp_folder, "urban_pop.tif")

            with rasterio.open(out_file, "w", **self.in_pop.meta) as out_urban:
                out_urban.write(cur_pop)

            res = rMisc.zonalStats(inA, out_file, minVal=0)
            res = pd.DataFrame(
                res,
                columns=[
                    "%s_%s_%s" % (out_name, name, x)
                    for x in ["SUM", "MIN", "MAX", "MEAN"]
                ],
            )
            try:
                final = final.join(res)
            except:
                final = res
        return final


class urban_country(object):
    """Extract and summarize urbanization in selected country, based on novel urbanization work of Mark Roberts and Shohei Nakamura"""

    def __init__(
        self,
        iso3,
        output_folder,
        country_bounds,
        pop_files,
        final_folder="",
        ghspop_suffix="",
    ):
        """Create object for managing input data for summarizing urban extents

        INPUT
        :param: iso3 - string describing iso3 code
        :param: output_folder - string path to folder to hold results
        :param: country_bounds - geopandas dataframe of admin0 boundary


        NAMING CONVENTION
        To save this renaming step on my side, which can also induce mistakes, would be possible for you Ben to rename the files in your code directly? This would be also helpful for all other countries we have to do, and for the 1km*1km rasters.
        My conventions are pretty simple. All rasters starts with the three lettres of the country and then _ as you do, and then 3 lettres for the variable, and possibly two figures for the year. So for instance for Tanzania, this is:
        tza_ele tza_slo tza_wat for elevation, slope and water
        tza_gpo tza_gbu for GHS population and built-up
        tza_upo15 and tza_upo18 for WorldPop population unconstrained
        tza_cpo15 and tza_cpo18 for WorldPop population constrained.
        Then for 1km*1km raster, names are the same except that the three lettres of the country's name are followed by 1k, ie tza1k_slo, tza1k_ele and so on.
        """
        self.iso3 = iso3
        self.out_folder = output_folder
        self.suffix = ghspop_suffix

        if final_folder == "":
            self.final_folder = os.path.join(self.out_folder, "FINAL_STANDARD")
        else:
            self.final_folder = os.path.join(self.out_folder, final_folder)
        if not os.path.exists(self.out_folder):
            os.makedirs(self.out_folder)
        if not os.path.exists(self.final_folder):
            os.makedirs(self.final_folder)

        self.dem_file = os.path.join(output_folder, "%s_ele.tif" % iso3.lower())
        self.slope_file = os.path.join(output_folder, "%s_slo.tif" % iso3.lower())
        self.desert_file = os.path.join(output_folder, "%s_des.tif" % iso3.lower())
        self.lc_file = os.path.join(output_folder, "%s_lc.tif" % iso3.lower())
        self.lc_file_h20 = os.path.join(output_folder, "%s_wat_lc.tif" % iso3.lower())
        self.ghsl_h20 = os.path.join(output_folder, "%s_wat.tif" % iso3.lower())
        self.ghspop_file = os.path.join(output_folder, "%s_gpo.tif" % iso3.lower())
        self.ghspop1k_file = os.path.join(output_folder, "%s1k_gpo.tif" % iso3.lower())
        self.ghsbuilt_file = os.path.join(output_folder, "%s_gbu.tif" % iso3.lower())
        self.ghssmod_file = os.path.join(output_folder, "%s_gsmod.tif" % iso3.lower())
        self.admin_file = os.path.join(output_folder, "%s_adm.tif" % iso3.lower())
        self.admin_shp = os.path.join(self.final_folder, "%s_adm.shp" % iso3.lower())
        self.pop_files = []
        # Copy and rename the population files
        for fileDef in pop_files:
            out_pop_file = os.path.join(output_folder, fileDef[1])
            self.pop_files.append(out_pop_file)
            if not os.path.exists(out_pop_file):
                tPrint(f"Clipping {fileDef[0]}")
                rMisc.clipRaster(
                    rasterio.open(fileDef[0]), country_bounds, out_pop_file
                )
            """
            if ghspop_suffix == '1k':
                if not self.ghspop1k_file in self.pop_files:
                    self.pop_files.append(self.ghspop1k_file)
            else:
            """
            if self.ghspop_file not in self.pop_files:
                self.pop_files.append(self.ghspop_file)

        self.pop_files = list(set(self.pop_files))
        # Write admin shapefile to output file
        self.inD = country_bounds
        if not os.path.exists(self.admin_shp):
            self.inD.to_file(self.admin_shp)

    def process_dem(self, global_dem=""):
        """Download DEM from AWS, calculate slope"""
        # Download DEM

        if not os.path.exists(self.dem_file) and global_dem == "":
            tPrint("Downloading DEM")
            elevation.clip(
                bounds=self.inD.total_bounds,
                max_download_tiles=90000,
                output=self.dem_file,
                product="SRTM3",
            )

        if not os.path.exists(self.dem_file) and not global_dem == "":
            tPrint("Downloading DEM")
            rMisc.clipRaster(rasterio.open(global_dem), self.inD, self.dem_file)

        # Calculate slope
        if not os.path.exists(self.slope_file) and os.path.exists(self.dem_file):
            tPrint("Calculating slope")
            in_dem = rasterio.open(self.dem_file)
            in_dem_data = in_dem.read()
            beau = richdem.rdarray(in_dem_data[0, :, :], no_data=in_dem.meta["nodata"])
            slope = richdem.TerrainAttribute(beau, attrib="slope_riserun")
            meta = in_dem.meta.copy()
            meta.update(dtype=slope.dtype)
            with rasterio.open(self.slope_file, "w", **meta) as outR:
                outR.write_band(1, slope)

    def extract_layers(
        self,
        global_landcover,
        global_ghspop,
        global_ghspop1k,
        global_ghbuilt,
        global_ghsl,
        global_smod,
    ):
        """extract global layers for current country"""
        # Extract desert from globcover
        if not os.path.exists(self.desert_file):
            tPrint("Extracting desert")
            if not os.path.exists(self.lc_file):
                rMisc.clipRaster(
                    rasterio.open(global_landcover), self.inD, self.lc_file
                )
            in_lc = rasterio.open(self.lc_file)
            inL = in_lc.read()
            lcmeta = in_lc.meta.copy()
            tempL = (inL == 200).astype(lcmeta["dtype"])
            lcmeta.update(nodata=255)
            with rasterio.open(self.desert_file, "w", **lcmeta) as out:
                out.write(tempL)
            os.remove(self.lc_file)

        # Extract water from globcover
        if not os.path.exists(self.lc_file_h20):
            tPrint("Extracting water")
            if not os.path.exists(self.lc_file):
                rMisc.clipRaster(
                    rasterio.open(global_landcover), self.inD, self.lc_file
                )
            in_lc = rasterio.open(self.lc_file)
            inL = in_lc.read()
            lcmeta = in_lc.meta.copy()
            tempL = (inL == 210).astype(lcmeta["dtype"])
            lcmeta.update(nodata=255)
            with rasterio.open(self.lc_file_h20, "w", **lcmeta) as out:
                out.write(tempL)
            os.remove(self.lc_file)

        # Extract water from GHSL
        if not os.path.exists(self.ghsl_h20):
            tPrint("Extracting water from GHSL")
            inR = rasterio.open(global_ghsl)
            if inR.crs.to_epsg() != self.inD.crs.to_epsg():
                tempD = self.inD.to_crs(inR.crs)
            else:
                tempD = inD
            ul = inR.index(*tempD.total_bounds[0:2])
            lr = inR.index(*tempD.total_bounds[2:4])
            # read the subset of the data into a numpy array
            window = (
                (float(lr[0]), float(ul[0] + 1)),
                (float(ul[1]), float(lr[1] + 1)),
            )
            data = inR.read(1, window=window, masked=False)
            data = data == 1
            b = tempD.total_bounds
            new_transform = rasterio.transform.from_bounds(
                b[0], b[1], b[2], b[3], data.shape[1], data.shape[0]
            )
            meta = inR.meta.copy()
            meta.update(
                driver="GTiff",
                width=data.shape[1],
                height=data.shape[0],
                transform=new_transform,
            )
            data = data.astype(meta["dtype"])
            with rasterio.open(self.ghsl_h20, "w", **meta) as outR:
                outR.write_band(1, data)

        # Extract GHS-Pop
        if not os.path.exists(self.ghspop_file):
            tPrint("Extracting GHS-POP")
            rMisc.clipRaster(rasterio.open(global_ghspop), self.inD, self.ghspop_file)

        # Extract GHS-Pop-1k
        if not os.path.exists(self.ghspop1k_file):
            tPrint("Extracting GHS-POP 1K: %s" % self.ghspop1k_file)
            rMisc.clipRaster(
                rasterio.open(global_ghspop1k), self.inD, self.ghspop1k_file
            )

        # Extract GHS-Built
        if not os.path.exists(self.ghsbuilt_file):
            tPrint("Clipping GHS-Built")
            rMisc.clipRaster(
                rasterio.open(global_ghbuilt), self.inD, self.ghsbuilt_file
            )

        # Extract GHS-SMOD
        if not os.path.exists(self.ghssmod_file):
            tPrint("Clipping GHS-SMOD")
            rMisc.clipRaster(rasterio.open(global_smod), self.inD, self.ghssmod_file)

        # Rasterize admin boundaries
        if not os.path.exists(self.admin_file):
            tPrint("Rasterizing admin boundaries")
            xx = rasterio.open(self.ghspop_file)
            res = xx.meta["transform"][0]
            tempD = self.inD.to_crs(xx.crs)
            shapes = ((row["geometry"], 1) for idx, row in tempD.iterrows())
            burned = features.rasterize(
                shapes=shapes,
                out_shape=xx.shape,
                fill=0,
                transform=xx.meta["transform"],
                dtype="int16",
            )
            meta = xx.meta.copy()
            meta.update(dtype=burned.dtype)
            with rasterio.open(self.admin_file, "w", **meta) as outR:
                outR.write_band(1, burned)

    def calculate_urban(self, urb_val=300, hd_urb_val=1500):
        """Calculate urban and HD urban extents from population files"""
        # Calculate urban extents from population layers
        ghs_R = rasterio.open(self.ghspop_file)
        for p_file in self.pop_files:
            final_pop = os.path.join(
                self.final_folder,
                os.path.basename(p_file).replace(
                    self.iso3.lower(), "%s%s" % (self.iso3.lower(), self.suffix)
                ),
            )
            print(final_pop)
            if "1k1k" in final_pop:
                final_pop = final_pop.replace("1k1k", "1k")
            final_urban = final_pop.replace(".tif", "_urban.tif")
            final_urban_hd = final_pop.replace(".tif", "_urban_hd.tif")
            urbanR = urban.urbanGriddedPop(final_pop)
            # Convert density values for urbanization from 1km resolution to current resolution
            in_raster = rasterio.open(final_pop)
            total_ratio = (in_raster.res[0] * in_raster.res[1]) / 1000000
            if not os.path.exists(final_urban):
                urban_shp = urbanR.calculateUrban(
                    densVal=(urb_val * total_ratio),
                    totalPopThresh=5000,
                    raster=final_urban,
                )
            if not os.path.exists(final_urban_hd):
                cluster_shp = urbanR.calculateUrban(
                    densVal=(hd_urb_val * total_ratio),
                    totalPopThresh=50000,
                    raster=final_urban_hd,
                    smooth=True,
                    queen=True,
                )

    def pop_zonal_admin(self, admin_layer):
        """calculate urban and rural

        :param: - admin_layer
        """
        for p_file in self.pop_files:
            pop_file = os.path.join(
                self.final_folder,
                os.path.basename(p_file).replace(
                    self.iso3.lower(), "%s%s" % (self.iso3.lower(), self.suffix)
                ),
            )
            if "1k1k" in pop_file:
                pop_file = pop_file.replace("1k1k", "1k")
            yy = summarize_population(pop_file, admin_layer)
            if yy.check_inputs():
                res = yy.calculate_zonal(out_name="")
                out_file = f"/home/wb411133/data/Projects/MR_Novel_Urbanization/Data/LSO_URBAN_DATA_new_naming/LSO_{os.path.basename(p_file)}.csv"
                try:
                    final = final.join(res)
                except:
                    final = res
            else:
                print("Error summarizing population for %s" % pop_file)
        admin_layer = admin_layer.reset_index()
        final = final.filter(regex="_SUM")
        final = final.join(admin_layer)
        final = final.drop(["geometry"], axis=1)
        return final

    def compare_pop_rasters(self, verbose=True):
        """read in and summarize population rasters"""
        all_res = []
        for pFile in self.pop_files:
            inR = rasterio.open(pFile)
            inD = inR.read()
            inD = inD[inD > 0]
            all_res.append([os.path.basename(pFile), inD.sum()])
            if verbose:
                print(f"{os.path.basename(pFile)}: {inD.sum()}")
        return all_res

    def standardize_rasters(self, include_ghsl_h20=True):
        """ """
        ghs_R = rasterio.open(self.ghspop_file)
        pFile = self.ghspop_file
        if self.suffix == "1k":
            ghs_R = rasterio.open(self.ghspop1k_file)
            pFile = self.ghspop1k_file
        file_defs = [
            # file, type, scale values
            [self.admin_file, "C", False],
            [self.desert_file, "C", False],
            [self.lc_file_h20, "C", False],
            [self.slope_file, "N", False],
            [self.dem_file, "N", False],
            [self.ghssmod_file, "N", False],
            [self.ghsbuilt_file, "N", False],
        ]

        if include_ghsl_h20:
            file_defs.append([self.ghsl_h20, "C", False])
            file_defs.append(
                [
                    self.ghsl_h20,
                    "N",
                    False,
                    os.path.join(
                        self.final_folder,
                        "%s%s_wat_p.tif" % (self.iso3.lower(), self.suffix),
                    ),
                ]
            )

        for cFile in self.pop_files:
            file_defs.append([cFile, "N", True])

        for file_def in file_defs:
            try:
                out_file = file_def[3]
            except:
                out_file = os.path.join(
                    self.final_folder,
                    os.path.basename(file_def[0]).replace(
                        self.iso3.lower(), "%s%s" % (self.iso3.lower(), self.suffix)
                    ),
                )
            if "1k1k" in out_file:
                out_file = out_file.replace("1k1k", "1k")
            if (file_def[0] == self.admin_file) and (os.path.exists(out_file)):
                os.remove(out_file)
            out_array = np.zeros(ghs_R.shape)
            if not os.path.exists(out_file) and os.path.exists(file_def[0]):
                in_raster = rasterio.open(file_def[0])
                in_r = in_raster.read()
                temp_nodata = type(in_r[0, 0, 0])(in_raster.meta["nodata"])
                in_r[in_r == temp_nodata] = 0
                rSample = rasterio.warp.Resampling.sum
                if file_def[1] == "C":
                    rSample = rasterio.warp.Resampling.nearest
                rasterio.warp.reproject(
                    in_r,
                    out_array,
                    src_transform=in_raster.meta["transform"],
                    dst_transform=ghs_R.meta["transform"],
                    src_crs=in_raster.crs,
                    dst_crs=ghs_R.crs,
                    src_nodata=in_raster.meta["nodata"],
                    dst_nodata=ghs_R.meta["nodata"],
                    resampling=rSample,
                )
                out_array[out_array == ghs_R.meta["nodata"]] = 0.0
                # scale and project file to GHS pop if defined so
                if file_def[0] == self.admin_file:
                    adminA = out_file
                    in_a = out_array
                    in_a_mask = in_a == 0

                # If values are to be scaled based on area change, do it here
                if file_def[2]:
                    out_array_sum = out_array.sum()
                    original_sum = in_r.sum()
                    total_ratio = original_sum / out_array_sum
                    self.total_ratio = total_ratio
                    out_array = out_array * total_ratio
                    out_array[out_array < 0] = ghs_R.meta["nodata"]

                # Set area outside national boundaries to nodata
                out_array[in_a_mask] = ghs_R.meta["nodata"]
                out_meta = ghs_R.meta.copy()
                out_meta.update(nodata=ghs_R.meta["nodata"])
                out_array = out_array.astype(out_meta["dtype"])
                with rasterio.open(out_file, "w", **out_meta) as outR:
                    outR.write_band(1, out_array)
            # Write no data layers to file
            out_no_data_file = os.path.join(
                self.final_folder, "NO_DATA_%s" % os.path.basename(file_def[0])
            )
            if not os.path.exists(out_no_data_file) and os.path.exists(file_def[0]):
                out_array = ghs_R.read() * 0
                in_raster = rasterio.open(file_def[0])
                in_r = in_raster.read()
                # create binary file defining no data area
                in_r = (in_r == in_raster.meta["nodata"]).astype(ghs_R.meta["dtype"])
                rasterio.warp.reproject(
                    in_r,
                    out_array,
                    src_transform=in_raster.meta["transform"],
                    dst_transform=ghs_R.meta["transform"],
                    src_crs=in_raster.crs,
                    dst_crs=ghs_R.crs,
                    src_nodata=in_raster.meta["nodata"],
                    dst_nodata=ghs_R.meta["nodata"],
                    resample=rasterio.warp.Resampling.nearest,
                )
                out_meta = ghs_R.meta.copy()
                with rasterio.open(out_no_data_file, "w", **out_meta) as outR:
                    outR.write(out_array)

        # Apply admin mask to population file
        gpo1R = rasterio.open(pFile)
        admR = rasterio.open(adminA)

        gpo1D = gpo1R.read()
        maskD = admR.read()

        gpo1D[gpo1D == gpo1R.meta["nodata"]] = 0
        gpo1D[maskD == admR.meta["nodata"]] = gpo1R.meta["nodata"]
        out_file = os.path.join(self.final_folder, os.path.basename(pFile))
        with rasterio.open(out_file, "w", **gpo1R.meta) as outR:
            outR.write(gpo1D)

    def evaluateOutput(self, admin_stats, commune_stats):
        """
        Check the outputs to determine if processing worked correctly

            1. compare population totals between raw, 250m and 1km data
            2. Calculate urbanization rate
            3. Water mask
               a. calculate overlap between water classes
               b. calculate overlap between water and population
               c. calculate overlap between water and urban

        https://ghsl.jrc.ec.europa.eu/documents/cfs01/V3/CFS_Ghana.pdf
        """
        stats_file = os.path.join(
            self.out_folder, "DATA_EVALUATION_%s_%s.txt" % (self.iso3, self.suffix)
        )
        with open(stats_file, "w") as out_stats:
            # Compare pop rasters
            pop_comparison = self.compare_pop_rasters(verbose=False)
            out_stats.write("***** Evaluate Total Population *****\n")
            for x in pop_comparison:
                out_stats.write(f"{x[0]}: {x[1]}\n")
            # define population and urbanization layers
            pop_file_defs = []
            for pop_file in self.pop_files:
                name = "GHS"
                if "upo" in pop_file:
                    name = "WP_U_%s" % pop_file[-6:-4]
                if "cpo" in pop_file:
                    name = "WP_C_%s" % pop_file[-6:-4]

                pop_file_base = os.path.basename(pop_file)
                if self.suffix == "1k":
                    pop_file_base = pop_file_base.replace(
                        self.iso3.lower(), "%s%s" % (self.iso3.lower(), self.suffix)
                    )
                    if "1k1k" in pop_file_base:
                        pop_file_base = pop_file_base.replace("1k1k", "1k")

                out_pop_file = os.path.join(self.final_folder, pop_file_base)
                urban_pop_file = out_pop_file.replace(".tif", "_urban.tif")
                hd_pop_file = out_pop_file.replace(".tif", "_urban_hd.tif")
                pop_file_defs.append([out_pop_file, urban_pop_file, hd_pop_file, name])
            out_stats.write("***** Evaluate Urbanization *****\n")
            for fileDef in pop_file_defs:
                pFile = fileDef[0]
                urb_file = fileDef[1]
                hd_file = fileDef[2]
                name = fileDef[3]
                try:
                    inPop = rasterio.open(pFile).read()
                    inPop = inPop * (inPop > 0)
                    inUrb = rasterio.open(urb_file).read()
                    inHd = rasterio.open(hd_file).read()

                    tPop = inPop.sum()
                    urbPop = (inPop * inUrb).sum()
                    hdPop = (inPop * inHd).sum()
                    out_stats.write(
                        f"{name}: TotalPop: {tPop.round(0)}, UrbanPop: {urbPop.round(0)}, HD Pop: {hdPop.round(0)}\n"
                    )
                    out_stats.write(
                        f"{name}: {((urbPop/tPop) * 100).round(2)}% Urban; {((hdPop/tPop) * 100).round(2)}% HD Urban\n"
                    )
                except:
                    print(f"Error processing {name}")
                    print(fileDef)

            # Summarize population in SMOD classes
            out_stats.write("***** Evaluate SMOD ******\n")
            smod_vals = [10, 11, 12, 13, 21, 22, 23, 30]
            inSMOD = rasterio.open(
                os.path.join(
                    self.final_folder,
                    os.path.basename(self.ghssmod_file).replace(
                        "%s" % self.iso3.lower(),
                        "%s%s" % (self.iso3.lower(), self.suffix),
                    ),
                )
            )
            smod = inSMOD.read()
            for pFile in self.pop_files:
                if "gpo" in pFile:
                    inPop = rasterio.open(pFile)
            pop = inPop.read()
            pop[pop < 0] = 0
            total_pop = pop.sum()
            total_per = 0
            for val in smod_vals:
                cur_smod = (smod == val).astype(int)
                cur_pop = pop * cur_smod
                total_curpop = cur_pop.sum()
                perUrban = total_curpop.sum() / total_pop * 100
                if val > 20:
                    total_per = total_per + perUrban
                out_stats.write(f"{val}: {perUrban}\n")
            out_stats.write(f"Total Urban: {total_per}\n")

            """3. Water mask
            """
            out_stats.write("***** Evaluate Water Intersection *****\n")
            # a. calculate overlap between water classes
            water_ghsl = os.path.join(
                self.final_folder, "%s%s_wat.tif" % (self.iso3.lower(), self.suffix)
            )
            water_lc = os.path.join(
                self.final_folder, "%s%s_wat_lc.tif" % (self.iso3.lower(), self.suffix)
            )
            inWG = rasterio.open(water_ghsl)
            wgData = inWG.read()
            wgData[wgData == inWG.meta["nodata"]] = 0
            inWLC = rasterio.open(water_lc)
            wlcData = inWLC.read()
            wlcData[wlcData == inWLC.meta["nodata"]] = 0
            combo = wgData + wlcData
            out_stats.write(
                f"WATER: GHSL count: {wgData.sum()}; LC count: {wlcData.sum()}; overlap: {(combo == 2).sum()}\n"
            )

            # b. calculate overlap between water and population
            out_stats.write("***** Evaluate Water Population Overlap *****\n")
            for fileDef in pop_file_defs:
                pop_file = fileDef[0]
                urb_file = fileDef[1]
                hd_file = fileDef[2]
                name = fileDef[3]

                cur_pop = rasterio.open(pop_file)
                curP = cur_pop.read()
                curP[curP == cur_pop.meta["nodata"]] = 0

                urb = rasterio.open(urb_file).read()
                hd = rasterio.open(hd_file).read()

                # c. calculate overlap between water and urban
                out_stats.write(
                    f"WATER {name} Population: TotalPop: {curP.sum().round()}, WaterPop GHSL: {(curP * wgData).sum().round()}, WaterPop LC: {(curP * wlcData).sum().round()}\n"
                )
                out_stats.write(
                    f"WATER {name} Urban Cells: TotalUrban Cells: {urb.sum().round()}, WaterUrban GHSL: {(urb * wgData).sum()}, WaterUrb LC: {(urb * wlcData).sum()}\n"
                )
                out_stats.write(
                    f"WATER {name} HD Cells: TotalPop: {hd.sum().round()}, WaterHD GHSL: {(hd * wgData).sum()}, WaterHD LC: {(hd * wlcData).sum()}\n"
                )

            # Summarize zonal stats files
            for sFile in [admin_stats, commune_stats]:
                if os.path.exists(sFile):
                    tPrint(sFile)
                    file_name = os.path.basename(sFile)
                    inD = pd.read_csv(sFile, index_col=0)
                    out_stats.write(f"***** Summarizing {file_name}\n")
                    bad_cols = [
                        "index",
                        "OBJECTID",
                        "WB_ADM1_CO",
                        "WB_ADM0_CO",
                        "WB_ADM2_CO",
                        "Shape_Leng",
                        "Shape_Area",
                    ]
                    for col in inD.columns:
                        if col not in bad_cols:
                            curD = inD[col]
                            try:
                                curD_sum = curD.loc[curD > 0].sum()
                                out_stats.write(f"{col}: {round(curD_sum)}\n")
                            except:
                                pass
