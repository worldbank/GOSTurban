# -*- coding: utf-8 -*-
import pandas as pd
import geopandas as gpd
import os
import numpy as np
from sklearn.neighbors import KDTree
import time

### Credit: The base code of STEP1 and STEP2 were coded by Alex Chunet ###


start_time = time.time()

pth = os.getcwd()
WGS = {"init": "epsg:4326"}
UTM = {"init": "epsg:32629"}
save_thresh = 100000  # save progress every [] rows
print_thresh = 10000  # print out calculation process every [] rows for each processor

cpuPower = 1 / 2
shpName = "/Niamey_data/DA_Niamey.shp"


###

f = pth + shpName

fil = gpd.read_file(f)
if fil.crs != WGS:
    fil = fil.to_crs(WGS)
fil = fil.to_crs(UTM)
fil["area"] = fil.area
fil["centroid"] = fil["geometry"].centroid
fil = fil.to_crs(WGS)
fil = fil[["PID", "centroid", "area"]]


# short = fil[:50000]
short = fil

area_dict = dict(zip(list(short.index), list(short["area"])))
matrix = list(
    zip(short.centroid.apply(lambda x: x.x), short.centroid.apply(lambda x: x.y))
)
KD_tree = KDTree(matrix)


###
def Main(passed_dict):
    # unpack passed dict into local variables for this thread.
    short = passed_dict["df"]
    thread_no = passed_dict["thread_no"]
    print_thresh = passed_dict["print_thresh"]
    save_thresh = passed_dict["save_thresh"]

    # set up some counters / timings
    t = time.time()
    counter = 1

    bundle = []

    # iterate through each row of the passed DataFrame of housing polygons.
    for index, row in short.iterrows():
        # identify the x and y coordinates of the house's centroid
        y = row.centroid.y
        x = row.centroid.x

        # Query the KD tree for the first 26 objects (1 will be the house itself.)
        # this returns a dataframe of the nearest 26 objects, their distances, and their indices.
        distances, indices = KD_tree.query([(x, y)], k=26)

        # Distance calculations - closest 5
        # here, we subset the distances frame for the first 5 neighbours, and calculate summary stats
        nearest_5_distances = list(distances[0])[1:6]  # subset / slice
        min_5 = min(
            nearest_5_distances
        )  # closest neighbour of the 5 closest (min distance to another building)
        max_5 = max(
            nearest_5_distances
        )  # furthest neighbour of the 5 closest (min distance to another building)
        mean_5 = np.mean(
            nearest_5_distances
        )  # average distance of centroids of 5 nearest neighbours
        median_5 = np.median(
            nearest_5_distances
        )  # median distance of centroids of 5 nearest neighbours
        dist_5_std = np.std(
            nearest_5_distances
        )  # standard deviation of centroids of 5 nearest neighbours

        # Distance calculations - closest 25
        # here, we subset the distances frame for the first 25 neighbours, and calculate summary stats
        nearest_25_distances = list(distances[0])[1:]
        min_25 = min(nearest_25_distances)
        max_25 = max(nearest_25_distances)
        mean_25 = np.mean(nearest_25_distances)
        median_25 = np.median(nearest_25_distances)
        dist_25_std = np.std(nearest_5_distances)

        # Areal calculations - closest 5
        # here, instead of the distances frame we generated via the KD tree, we use the area_dict
        # and query it with the indices from the KD tree step
        indices_5 = list(indices[0])[1:6]
        areas = [area_dict[x] for x in indices_5]
        area_5_mean = np.mean(areas)  # mean area of 5 nearest neighbours
        area_5_med = np.median(areas)  # median area of 5 nearest neighbours
        area_5_stdev = np.std(
            areas
        )  # standard deviation of area of 5 nearest neighbours

        # Areal calculations - closest 25
        # repeat above block for closest 25
        indices_25 = list(indices[0])[1:]
        areas = [area_dict[x] for x in indices_25]
        area_25_mean = np.mean(areas)
        area_25_med = np.median(areas)
        area_25_stdev = np.std(areas)

        # Count
        # here we turn the process on its head, and identify all objects within certain distance thresholds
        count_25m = KD_tree.query_radius([(x, y)], r=25, count_only=True)[
            0
        ]  # count of buildings in 25m radius
        count_50m = KD_tree.query_radius([(x, y)], r=50, count_only=True)[
            0
        ]  # count of buildings in 50m radius
        count_100m = KD_tree.query_radius([(x, y)], r=100, count_only=True)[
            0
        ]  # count of buildings in 100m radius

        # add these stats to a dictionary called 'ans'
        ans = {
            "PID": row.PID,
            "area": row.area,
            "D5_min": min_5,
            "D5_max": max_5,
            "D5_mean": mean_5,
            "D5_med": median_5,
            "D5_std": dist_5_std,
            "A5_mean": area_5_mean,
            "A5_med": area_5_med,
            "A5_std": area_5_stdev,
            "D25_min": min_25,
            "D25_max": max_25,
            "D25_mean": mean_25,
            "D25_med": median_25,
            "D25_std": dist_25_std,
            "A25_mean": area_25_mean,
            "A25_med": area_25_med,
            "A25_std": area_25_stdev,
            "Count_25m": count_25m,
            "Count_50m": count_50m,
            "Count_100m": count_100m,
        }

        bundle.append(ans)

        # keep track of progress via this row
        if counter % print_thresh == 0:
            print("%s rows completed at %s" % (counter, time.ctime()))

        """
        # this functionality saves progress in case the process cannot be finished in one sitting.
        # ideally, finish the processing in one sitting.
        old = 0
        if counter % save_thresh == 0:
            saver = pd.DataFrame(bundle)
            saver = saver[list(bundle[0].keys())]
            if saver.crs != WGS:
                saver = saver.to_crs(WGS)
            saver = saver.set_index('PID')
            saver = saver.set_index('PID')
            saver['geometry'] = saver['geometry']
            saver = gpd.GeoDataFrame(saver, geometry = 'geometry', crs = WGS)
            saver.to_file(os.path.join(pth, 'output_%s_to_%s_thread_%s.shp' % (old, counter, thread_no)), driver = 'ESRI Shapefile')
            bundle = []
            old = counter
        """

        counter += 1

    return bundle

    print("Task completed in %s seconds" % (time.time() - t))


###


# threads = multiprocessing.cpu_count()  # limit this line if on the JNB to avoid consuming 100% of resources!
"""
cpu = multiprocessing.cpu_count()
threads = int(cpu * cpuPower)

d = []

for i in range(1, (threads+1)):
    len_total_df = len(short)
    chunk = int(np.ceil(len_total_df / threads))
    d_f = short[(chunk*(i-1)):(chunk*i)]

    processor_input_dict = {
        'df':d_f,
        'thread_no':i,
        'print_thresh':print_thresh,
        'save_thresh':save_thresh
    }

    d.append(processor_input_dict)

with Pool(threads) as pool:
        results = pool.map(Main, d, chunksize = 1)

"""


d = {}

d = {
    "df": short,
    "thread_no": 1,
    "print_thresh": print_thresh,
    "save_thresh": save_thresh,
}


result = Main(d)


out_df = pd.DataFrame(result)

orig_fil = gpd.read_file(f)
if orig_fil.crs != WGS:
    orig_fil = orig_fil.to_crs(WGS)
orig_fil = orig_fil.set_index("PID")

out_df = out_df.set_index("PID")
out_df["geometry"] = orig_fil["geometry"]
out_df = gpd.GeoDataFrame(out_df, geometry="geometry", crs=WGS)
out_df.to_file(os.path.join(pth, "buildings_altered.shp"), driver="ESRI Shapefile")


elapsed_time = (time.time() - start_time) / 60
print("elapsed_time:{0}".format(elapsed_time) + "[Min]")
