# OpenBuildings2FeatureClass
This script is to convert the CSV file(s) of [Google Open Buildings](https://sites.research.google/open-buildings/) to a Feature Class.

![Layout2](https://user-images.githubusercontent.com/64405484/137813865-0abd8f0c-ff15-4980-9251-042a8f9dc66b.png)
An example map rendered in ArcGIS Pro (Cairo Metropolitan Area)

## How to use
This script uses ArcPy modules, so your environment should have ArcPy library. Simply, load the script to your Tool Box on your ArcGIS Pro project and run it. The target Open Buildings CSV file must be stored in the folder where the script is located.

If you want to test the script with a small chunk of a full CSV, modify the code:

```python
df_test = df_conf.iloc[0:100, :].copy()
df_test.reset_index(inplace=True, drop=True)

for i, r in df_conf.iterrows():
```
For example, iloc[0:100] will retirieve the first 100 records from the original data. df_conf should be replaced by df_test.

## NOTE

* Each CSV file based on [S2 geometry cells](https://s2geometry.io/) can contain a huge amount of geometries (+10 million), so it is highly recommended to limit the geographical scope of your CSV file. This [download region polygons](https://colab.research.google.com/github/google-research/google-research/blob/master/building_detection/open_buildings_download_region_polygons.ipynb#scrollTo=fwxfj3B1qUWu) tool developed by the Open Buildings Google team will help you to define the target geographical extent when you download the CSV file.
* Process speed: Approximately **0.5 million geometries / about 5 hours** with Windows 10 - AMD Ryzen 9 3900X 12-Core Processor 3.79 GHz, 32GB RAM.
* The data could contain invalid geometries (basically 'EMPTY' geometries). These invalid geometries will be automatically removed from the resulted feature class.
