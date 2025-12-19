# -------------------------------------------------------------------------------
# Calculate urban areas from gridded population data
# Benjamin P Stewart, April 2019
#   Purpose is to create high density urban clusters and urban cluster above minimum
#   density and total population thresholds
# -------------------------------------------------------------------------------

import geojson
import json
import time

import rasterio
import geopandas as gpd
import pandas as pd
import numpy as np
import GOSTrocks.rasterMisc as rMisc

from scipy import stats
from scipy import ndimage
from scipy.ndimage import generic_filter
from scipy.sparse.csgraph import connected_components
from rasterio import features
from rasterio.features import rasterize
from shapely.geometry import shape, Polygon
from geopy.geocoders import Nominatim
from rasterstats import zonal_stats

"""prints the time along with the message"""


def tPrint(s):
    print("%s\t%s" % (time.strftime("%H:%M:%S"), s))


def summarize_urban_pop(inD, urbanLyr, pop_lyr, reproj=True, calc_pop=True):
    """Summarize population and urban population within the defined polygonal dataset (inD)

    Parameters
    ----------
    inD : gpd.GeoDataFrame
        Input polygon dataset to summarize population within
    urbanLyr : rasterio.DatasetReader
        Rasterio object representing urban extent raster as binary values
    pop_lyr : rasterio.DatasetReader
        Rasterio object representing population raster to summarize
    """
    if inD.crs != urbanLyr.crs and reproj:
        inD = inD.to_crs(urbanLyr.crs)

    if urbanLyr.shape != pop_lyr.shape:
        raise ValueError("Urban and population layers must be the same shape")

    # Summarize population within polygons
    if calc_pop:
        res = rMisc.zonalStats(inD, pop_lyr, minVal=0, return_df=True)
        inD["Total_Pop"] = res["SUM"]

    # Combine population and urban layers to get urban population
    urban_data = urbanLyr.read(1)
    pop_data = pop_lyr.read(1)
    urban_pop_data = pop_data * (urban_data > 0)

    with rMisc.create_rasterio_inmemory(
        urbanLyr.profile, urban_pop_data
    ) as urban_pop_lyr:
        urban_res = rMisc.zonalStats(inD, urban_pop_lyr, minVal=0, return_df=True)

    inD["Urban_Pop"] = urban_res["SUM"]
    return inD


def geocode_cities(urban_extents):
    """Generate names for polygon urban extents

    :param urban_extents: geopandas dataframe of polygons to be named. Need to be in epsg:4326
    """
    geolocator = Nominatim(user_agent="new_app")
    all_res = []
    for idx, row in urban_extents.iterrows():
        res = geolocator.reverse(
            query=(row["geometry"].centroid.y, row["geometry"].centroid.x),
            language="en",
            zoom=10,
        )
        all_res.append(res)

    urban_extents["City"] = ""
    urban_extents["State"] = ""
    urban_extents["Country"] = ""

    for idx, row in urban_extents.iterrows():
        res = all_res[idx]
        try:
            urban_extents.loc[idx, "City"] = res.raw["address"]["city"]
        except Exception:
            continue
        try:
            urban_extents.loc[idx, "State"] = res.raw["address"]["state"]
        except Exception:
        except Exception:
            pass
        try:
            urban_extents.loc[idx, "Country"] = res.raw["address"]["country"]
        except Exception:
        except Exception:
            pass
    return urban_extents


class urbanGriddedPop(object):
    def __init__(self, inRaster):
        """
        Create urban definitions using gridded population data.

        :param inRaster: string or rasterio object representing gridded population data
        """
        if isinstance(inRaster, str):
        if isinstance(inRaster, str):
            self.inR = rasterio.open(inRaster)
        elif isinstance(inRaster, rasterio.DatasetReader):
            self.inR = inRaster
        else:
            raise (
                ValueError(
                    "Input raster dataset must be a file path or a rasterio object"
                )
            )

    def calculateDegurba(
        self,
        urbDens=300,
        hdDens=1500,
        urbThresh=5000,
        hdThresh=50000,
        minPopThresh=50,
        out_raster="",
        print_message="",
        verbose=False,
    ):
        """Calculate complete DEGURBA classification based on gridded population data
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
        """

        popRaster = self.inR
        data = popRaster.read()
        urban_raster = data * 0
        final_raster = data[0, :, :] * 0 + 11

        urban_raster[np.where(data > hdDens)] = 30
        idx = 0
        urban_raster = urban_raster.astype("int16")
        allFeatures = []

        if verbose:
            tPrint(f"{print_message}: Smoothing Urban Clusters")

        # Smooth the HD urban clusters
        def modal(P):
            mode = stats.mode(P)
            return mode.mode[0]

        smooth_urban = generic_filter(urban_raster[0, :, :], modal, (3, 3))
        yy = np.dstack([smooth_urban, urban_raster[0, :, :]])
        urban_raster[0, :, :] = np.amax(yy, axis=2)

        # Analyze the high density shapes
        if verbose:
            tPrint(f"{print_message}: extracting HD clusters")

        for cShape, value in features.shapes(
            urban_raster, transform=popRaster.transform
        ):
            if idx % 1000 == 0 and verbose:
                tPrint("%s: Creating Shape %s" % (print_message, idx))
            idx = idx + 1
            if value > 0:
                # Remove holes from urban shape
                xx = shape(cShape)
                xx = Polygon(xx.exterior)
                cShape = xx.__geo_interface__
                # If the shape is urban, calculate total pop
                # If the shape is urban, calculate total pop
                mask = rasterize(
                    [(cShape, 0)],
                    out_shape=data[0, :, :].shape,
                    fill=1,
                    transform=popRaster.transform,
                )
                inData = np.ma.array(data=data, mask=mask.astype(bool))
                pop = np.nansum(inData)

                val = 0
                if pop > urbThresh:
                    ### TODO - if the totalpop is < 50k, may need to unsmooth the shape
                    val = 23
                if pop > hdThresh:
                    val = 30

                # Burn value into the final raster
                mask = (mask ^ 1) * val
                yy = np.dstack([final_raster, mask])
                final_raster = np.amax(yy, axis=2)
                allFeatures.append(
                    [idx, pop, val, shape(geojson.loads(json.dumps(cShape)))]
                )

        HD_raster = final_raster

        urban_raster = data * 0
        final_raster = data[0, :, :] * 0 + 11
        urban_raster[np.where(data > urbDens)] = 22
        urban_raster = urban_raster.astype("int16")
        # Analyze the high density shapes
        if verbose:
            tPrint(f"{print_message}: extracting URBAN clusters")

        for cShape, value in features.shapes(
            urban_raster, transform=popRaster.transform, connectivity=8
        ):
            if idx % 1000 == 0 and verbose:
                tPrint("%s: Creating Shape %s" % (print_message, idx))
            idx = idx + 1
            if value > 0:
                # If the shape is urban, calculate total pop
                # If the shape is urban, calculate total pop
                mask = rasterize(
                    [(cShape, 0)],
                    out_shape=data[0, :, :].shape,
                    fill=1,
                    transform=popRaster.transform,
                )
                inData = np.ma.array(data=data, mask=mask.astype(bool))
                pop = np.nansum(inData)
                val = 0
                if pop > 500:
                    val = 13
                if pop > urbThresh:
                    val = 21
                # Burn value into the final raster
                mask = (mask ^ 1) * val
                yy = np.dstack([final_raster, mask])
                final_raster = np.amax(yy, axis=2)
                allFeatures.append(
                    [idx, pop, val, shape(geojson.loads(json.dumps(cShape)))]
                )
        URB_raster = final_raster

        # Combine the urban layers
        yy = np.dstack([HD_raster, URB_raster])
        final_raster = np.amax(yy, axis=2)
        final_raster[
            (final_raster == 11)
            & (data[0, :, :] > minPopThresh)
            & (data[0, :, :] < urbDens)
        ] = 12

        if verbose:
            tPrint(f"{print_message}: performing distance calculations")

        # Identify the urban areas of class 22 by measuring distance to other features
        feats = allFeatures
        sel = pd.DataFrame(feats, columns=["ID", "POP", "CLASS", "geometry"])
        sel = gpd.GeoDataFrame(sel, geometry="geometry", crs=self.inR.crs)
        to_be = sel.loc[sel["CLASS"] == 21]
        to_be = to_be.loc[to_be["POP"] < hdThresh]
        distance = sel.loc[sel["CLASS"].isin([21, 23])]
        dist_shp = distance.sindex

        def calc_nearest(x, dist_gpd, dist_idx):
            xx = dist_gpd.iloc[list(dist_idx.nearest([x.centroid.x, x.centroid.y], 2))]
            dists = xx["geometry"].apply(lambda y: y.distance(x))
            try:
                return min(dists[dists > 0])
            except Exception:
                return 0

        to_be["dist"] = to_be["geometry"].apply(
            lambda x: calc_nearest(x, distance, dist_shp)
        )
        features_22 = to_be.loc[to_be["dist"] > 3000]

        # Burn features into output raster
        cShape = features_22.unary_union.__geo_interface__
        mask = rasterize(
            [(cShape, 0)],
            out_shape=data[0, :, :].shape,
            fill=1,
            transform=popRaster.transform,
        )
        mask_vals = (mask ^ 1) * 22

        final_raster = (final_raster * mask) + mask_vals

        if len(out_raster) > 0:
            out_metadata = popRaster.meta.copy()
            out_metadata["dtype"] = urban_raster.dtype
            out_metadata["nodata"] = -999
            final_raster = final_raster.astype(out_metadata["dtype"])
            with rasterio.open(out_raster, "w", **out_metadata) as rOut:
                rOut.write_band(1, final_raster)

        return {
            "raster": final_raster,
            "shapes": allFeatures,
            "HD": HD_raster,
            "URB": URB_raster,
        }

    def calculateUrban(
        self,
        densVal=300,
        totalPopThresh=5000,
        smooth=False,
        verbose=False,
        queen=False,
        raster="",
        raster_pop="",
        print_message="",
        sieve=False,
        sieve=False,
    ):
        """Generate urban extents from gridded population data through the application of a minimum
            density threshold and a minimum total population threshold

        Parameters
        ----------
        densVal : int, optional
            Minimum density value to be counted as urban, by default 300
        totalPopThresh : int, optional
            Minimum total settlement population to be considered urban, by default 5000
        smooth : bool, optional
            Whether to run a single modal smoothing function, by default False
        verbose : bool, optional
            Whether to print progress messages, by default False
        queen : bool, optional
            Whether to dissolve final shape to connect queen's contiguity, by default False
        raster : str, optional
            Path to create a boolean raster of urban and not, by default ""
        raster_pop : str, optional
            Path to create a raster of the population layer only in the urban areas, by default ""
        print_message : str, optional
            Message to print during processing, by default ""
        sieve : bool, optional
            Whether to apply a sieve filter to the urban raster, by default False

        Returns
        -------
        gpd.GeoDataFrame
            GeoDataFrame of the urban extents
        """
        popRaster = self.inR
        data = popRaster.read()[0, :, :]
        data = popRaster.read()[0, :, :]
        urbanData = (data > densVal) * 1
        urbanData = urbanData.astype("int16")

        if verbose:
            tPrint("%s: Read in urban data" % print_message)
        if sieve:
            sieve_size = round(
                totalPopThresh / data.max()
            )  # the minimum number of pixels to reach the totalPopThresh at max density
            sieve_size = round(
                totalPopThresh / data.max()
            )  # the minimum number of pixels to reach the totalPopThresh at max density
            urbanData = features.sieve(urbanData, size=sieve_size)


        # create output array to store urban raster
        urban_raster = urbanData * 0
        all_shps = []


        def calculate_urban_with_pop(curD, transform, thresh):
            """Calculate urban areas based on population threshold
            """Calculate urban areas based on population threshold

            Parameters
            ----------
            curD : numpy.ndarray
                Binary array of urban areas based on density threshold
            transform : Affine
                Affine transformation for the raster
            thresh : int
                Minimum total population threshold for urban areas

            Returns
            -------
            list of [numpy.ndarray, gpd.GeoDataFrame]
                urban raster and geodataframe of urban areas with population above the threshold
            """
            for cShape, value in features.shapes(
                curD, transform=transform, mask=curD.astype(bool)
            ):
            for cShape, value in features.shapes(
                curD, transform=transform, mask=curD.astype(bool)
            ):
                if value == 1:
                    all_shps.append(shape(cShape))

            # Create geodataframe of all potential urban areas
            potential_urban_areas = gpd.GeoDataFrame(
                geometry=all_shps, crs=popRaster.crs
            )
            potential_urban_areas = gpd.GeoDataFrame(
                geometry=all_shps, crs=popRaster.crs
            )
            # Calculate population within each potential urban area
            urban_pop = zonal_stats(
                potential_urban_areas,
                data,
                affine=popRaster.transform,
                stats=["sum"],
                nodata=0,
            )
            potential_urban_areas["pop"] = [up["sum"] for up in urban_pop]
            # Select only those urban areas above the population threshold
            selected_urban_areas = potential_urban_areas[
                potential_urban_areas["pop"] >= thresh
            ]
            urban_pop = zonal_stats(
                potential_urban_areas,
                data,
                affine=popRaster.transform,
                stats=["sum"],
                nodata=0,
            )
            potential_urban_areas["pop"] = [up["sum"] for up in urban_pop]
            # Select only those urban areas above the population threshold
            selected_urban_areas = potential_urban_areas[
                potential_urban_areas["pop"] >= thresh
            ]
            # Rasterize the selected urban areas to create the final urban raster
            urban_raster = rasterize(
                [(geom, 1) for geom in selected_urban_areas.geometry],
                out_shape=data.shape,
                fill=0,
                transform=popRaster.transform,
                transform=popRaster.transform,
            )
            return [urban_raster, selected_urban_areas]

        urban_raster, urban_areas = calculate_urban_with_pop(
            urbanData, popRaster.transform, totalPopThresh
        )
            return [urban_raster, selected_urban_areas]

        urban_raster, urban_areas = calculate_urban_with_pop(
            urbanData, popRaster.transform, totalPopThresh
        )

        if smooth:
            inD = urban_raster
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
            urban_raster, urban_areas = calculate_urban_with_pop(
                urban_raster, popRaster.transform, totalPopThresh
            )
            urban_raster, urban_areas = calculate_urban_with_pop(
                urban_raster, popRaster.transform, totalPopThresh
            )

        # Create output rasters if specified
        if len(raster):
            out_metadata = popRaster.meta.copy()
            urban_raster = urban_raster.astype(rasterio.uint8)
            out_metadata["dtype"] = urban_raster.dtype
            out_metadata["nodata"] = 0
            out_metadata["compress"] = "lzw"
            with rasterio.open(raster, "w", **out_metadata) as rOut:
                rOut.write_band(1, urban_raster)

        if len(raster_pop):
            out_metadata = popRaster.meta.copy()
            urban_pop = data * urban_raster
            with rasterio.open(raster_pop, "w", **out_metadata) as rOut:
                rOut.write_band(1, urban_pop)

        if queen:
            urban_areas["geometry"] = urban_areas.buffer((popRaster.res[0] / 2))
            s = urban_areas["geometry"]
            overlap_matrix = s.apply(lambda x: s.intersects(x)).values.astype(int)
            n, ids = connected_components(overlap_matrix)
            urban_areas["group"] = ids
            urban_areas = urban_areas.dissolve(by="group", aggfunc="sum")

        return urban_areas
