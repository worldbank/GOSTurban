import multiprocessing

import rasterio
import rasterio.features

import pandas as pd
import numpy as np

from GOSTrocks.misc import tPrint
from shapely.geometry import shape
from shapely.wkt import loads


def _mp_lei(curRxx, transformxx, idx_xx, old_list=[4, 5, 6], new_list=[3], buffer_dist=300):
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
    old_list,
    new_list,
    buffer_dist=300,
    measure_crs=None,
    idx_col=None,
    verbose=False
):
    """ Calculate the Landscape Expansion Index (LEI) from a categorical dataset 
        for each polygonal feature in inD

    Parameters
    ----------
    inD : geopands.GeoDataFrame
        Feature dataset for which to calculate LEI
    inR : rasterio.DatasetReader
        Raster of built area evolution data
    old_list : list, optional
        values in inR to be considered baseline (or t0)
    new_list : list, optional
       values in inR to be considered new urban areas
    buffer_dist : int, optional
        distance to search around the newly developed area from which to search for existing built area, by default 300
    measure_crs : int, optional
        CRS number to use for measurement, by default None
    idx_col : str, optional
        Column name to use as index, by default None
    verbose : bool, optional
        Whether to print progress messages, by default False

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the LEI results
    """
    if inD.crs != inR.crs:
        inD = inD.to_crs(inR.crs)

    if measure_crs is not None:
        measureD = inD.to_crs(measure_crs)

    # For grid cells, extract the GHSL and calculate
    in_vals = []
    if verbose:
        tPrint("***** Preparing values for multiprocessing")
    for idx, row in inD.iterrows():
        if idx % 100 == 0 and verbose:
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

    
    nCores = multiprocessing.cpu_count() - 1
    
    if verbose:
        tPrint("***** starting multiprocessing")
    with multiprocessing.Pool(nCores) as pool:
        res = pool.starmap(_mp_lei, in_vals)

    res = pd.DataFrame(res)
    res = res.reset_index()
    res.index = res["idx"]
    # res.drop(['idx'], axis=1, inplace=True)
    return res


def calculate_LEI(inputGHSL, old_list, new_list, buffer_dist=300, transform=""):
    """Calculate Landscape Expansion Index (LEI) through comparison of categorical values in a single raster dataset.

    Parameters
    ----------
    inputGHSL : str or rasterio.DatasetRaster or numpy.array
        Landcover dataset containing categorical values
    old_list : list of integers
        values in inputGHSL to be considered baseline (or t0)
    new_list : list of integers
        Values in inputGHSL to be considered new urban areas
    buffer_dist : int, optional
        Distance to search around the newly developed area from which to search for existing built area, by default 300
    transform : str, optional
        Raster transform information, by default ""

    Returns
    -------
    array of [curShape, oldArea, totalArea]
        results for each new urban area found in the dataset; curShape is the geometry of the new urban area,
        oldArea is the amount of old urban area found within buffer_dist of the new area, totalArea is the total area
        within buffer_dist of the new area.
    """ 
    
    if isinstance(inputGHSL, str):
        inRaster = rasterio.open(inputGHSL)
        inR = inRaster.read()
        transform = inRaster.transform
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

    Parameters
    ----------
    in_file : string path or pandas.DataFrame
        LEI results generated from calculate_LEI above
    leap_val : float, optional
        LEI value below which areas are considered to be leapfrog, defaults to 0.05
    exp_val : float, optional
        LEI value above which areas are considered to be infill, defaults to 0.9
    Returns
    -------
    pd.DataFrame
        pandas groupby row summarizing area in m2 of leapfrog, expansion, and infill areas
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

    return xx["area"].sum()
