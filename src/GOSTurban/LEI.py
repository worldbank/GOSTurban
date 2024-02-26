import multiprocessing

import rasterio
import rasterio.features

import pandas as pd
import numpy as np

from GOSTRocks.misc import tPrint
from shapely.geometry import shape
from shapely.wkt import loads


def mp_lei(
    curRxx, transformxx, idx_xx, old_list=[4, 5, 6], new_list=[3], buffer_dist=300
):
    """calculate and summarize LEI for curRxx, designed for use in multiprocessing function"""
    curRes = calculate_LEI(
        curRxx,
        transform=transformxx,
        old_list=old_list,
        new_list=new_list,
        buffer_dist=buffer_dist,
    )
    xx = pd.DataFrame(curRes, columns=["geometry", "old", "total"])
    xx["LEI"] = xx["old"] / xx["total"]
    final = summarize_LEI(xx)
    final["idx"] = idx_xx
    return final


def lei_from_feature(
    inD,
    inR,
    old_list=[4, 5, 6],
    new_list=[3],
    buffer_dist=300,
    transform="",
    nCores=0,
    measure_crs=None,
    idx_col=None,
):
    """Calculate LEI for each feature in inD, leveraging multi-processing, based on the built area in inR

    INPUT
    inD [geopandas]
    inR [rasterio]
    [optional] nCores [int] - number of cores to use in multi-processing
    [optional] measure_crs [string] - string to convert all data to a CRS where distance and area measurements don't suck ie - "ESRI:54009"
    ... see calculate_LEI for remaining arguments
    """
    if inD.crs != inR.crs:
        inD = inD.to_crs(inR.crs)

    if measure_crs is not None:
        measureD = inD.to_crs(measure_crs)

    lei_results = {}
    # For grid cells, extract the GHSL and calculate
    in_vals = []
    tPrint("***** Preparing values for multiprocessing")
    for idx, row in inD.iterrows():
        if idx % 100 == 0:
            tPrint(f"{idx} of {inD.shape[0]}: {len(in_vals)}")
        ul = inR.index(*row["geometry"].bounds[0:2])
        lr = inR.index(*row["geometry"].bounds[2:4])
        # read the subset of the data into a numpy array
        window = ((float(lr[0]), float(ul[0] + 1)), (float(ul[1]), float(lr[1] + 1)))
        curR = inR.read(1, window=window)
        if (np.isin(curR, old_list).sum() > 2) & (np.isin(curR, new_list).sum() > 2):
            if measure_crs is None:
                transform = rasterio.transform.from_bounds(
                    *row["geometry"].bounds, curR.shape[0], curR.shape[1]
                )
            else:
                transform = rasterio.transform.from_bounds(
                    *measureD.loc[idx, "geometry"].bounds, curR.shape[0], curR.shape[1]
                )
            cur_idx = idx
            if idx_col:
                cur_idx = row[idx_col]
            in_vals.append([curR, transform, cur_idx, old_list, new_list, buffer_dist])

    if nCores == 0:
        nCores = multiprocessing.cpu_count()
    tPrint("***** starting multiprocessing")
    with multiprocessing.Pool(nCores) as pool:
        res = pool.starmap(mp_lei, in_vals)

    res = pd.DataFrame(res)
    res = res.reset_index()
    res.index = res["idx"]
    # res.drop(['idx'], axis=1, inplace=True)
    return res


def calculate_LEI(inputGHSL, old_list, new_list, buffer_dist=300, transform=""):
    """Calculate Landscape Expansion Index (LEI) through comparison of categorical values in a single raster dataset.

    :param inputGHSL: Path to a geotiff or a rasterio object, or a numpy array containing the categorical
        data used to calculate LEI
    :type inputGHSL: rasterio.DatasetReader
    :param old_list: Values in built area raster to consider old urban.
    :type old_list: list of ints
    :param new_list: Values in built area raster to consider new urban
    :type new_list: list of ints
    :param buffer_dist: distance to buffer new urban areas for comparison to old urban extents, defaults to 300 (m)
    :type buffer_dist: int, optional
    :param transform: rasterio transformation object. Required if inputGHSL is a numpy array, defaults to ''
    :type transform: str, optional
    :returns: individual vectors of new built areas with LEI results. Each item is a single new built feature with three columns:
                1. geometry of the new built area feature
                2. number of pixels in new built area donut from old built area
                3. area of new built area buffer

    :example:
        # This calculates the LEI between 1990 and 2000 in the categorical GHSL
        lei_raw = calculate_LEI(input_ghsl, old_list = [5,6], new_list=[4])
        lei_90_00 = pd.DataFrame(lei_raw, columns=['geometry', 'old', 'total'])
        lei_90_00['LEI'] = lei_90_00['old'] / lei_90_00['total']
        lei_90_00.head()
    """
    if isinstance(inputGHSL, str):
        inRaster = rasterio.open(inputGHSL).read()
        inR = inRaster.read()
        transform = inR.transform
    elif isinstance(inputGHSL, rasterio.DatasetReader):
        inR = inputGHSL.read()
    else:
        inR = inputGHSL
    if len(inR.shape) == 2:
        inR = inR.reshape(1, inR.shape[0], inR.shape[1])
    newR = (np.isin(inR, new_list)).astype("int")
    oldR = (np.isin(inR, old_list)).astype("int")
    allVals = []
    for geom, value in rasterio.features.shapes(
        newR.astype("uint8"), transform=transform
    ):
        if value == 1:
            # Convert the geom to a shape and buffer by 300 metres
            curShape = shape(geom)
            bufferArea = curShape.buffer(buffer_dist)
            # Clip out the original shape to leave just the donut
            try:
                donutArea = bufferArea.difference(curShape)
            except:
                bufferArea = bufferArea.buffer(0)
                curShape = curShape.buffer(0)
                donutArea = bufferArea.difference(curShape)
            # Rasterize donut shape
            shapes = [(donutArea, 1)]
            burned = rasterio.features.rasterize(
                shapes=shapes,
                fill=0,
                out_shape=(oldR.shape[1], oldR.shape[2]),
                transform=transform,
            )
            # Multiply the new raster by the old urban data to get the total
            #     amount of old area in the buffer around the new urban area
            oldArea = (oldR[0, :, :] * burned).sum()
            totalArea = burned.sum()
            allVals.append([curShape, oldArea, totalArea])

    return allVals


def summarize_LEI(in_file, leap_val=0.05, exp_val=0.9):
    """Summarize the LEI results produced by self.calculate_LEI

    :param in_file: LEI results generated from calculate_LEI above
    :type in_file: string path to csv file or pandas dataframe
    :param leap_val: LEI value below which areas are considered to be leapfrog, defaults to 0.05
    :type leap_val: float, optional
    :param exp_val: LEI value above which areas are considered to be infill, defaults to 0.9
    :type exp_val: float, optional
    """

    """

    in_file [string path or datafrane]:
    leap_val [float]:
    exp_val [float]:

    returns
    [pandas groupby row]

    example

    for res_file in all_results_files:
        res = summarize_LEI(res_file)
        baseName = os.path.basename(os.path.dirname(res_file))
        summarized_results[baseName] = res

    all_results = pd.DataFrame(summarized_results).transpose()
    """
    if isinstance(in_file, str):
        res = pd.read_csv(in_file)
        res["area"] = res["geometry"].apply(lambda x: loads(x).area)
    else:
        res = in_file
        if "area" not in res.columns:
            res["area"] = res["geometry"].apply(lambda x: x.area)

    def calculate_LEI(val, leap_val, exp_val):
        if val <= leap_val:
            return "Leapfrog"
        elif val < exp_val:
            return "Expansion"
        else:
            return "Infill"

    res["class"] = res["LEI"].apply(lambda x: calculate_LEI(x, leap_val, exp_val))
    xx = res.groupby("class")
    return xx.sum()["area"]
