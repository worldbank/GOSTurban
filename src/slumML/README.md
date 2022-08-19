# slumML

## 1. slumML main component

### 1.1. Sample data preparation
(1) 5–10 sample areas per area character of interest (e.g., slum, commercial, middle-class resident, etc). If you’d like to cluster your target city into four classes (slum, Commercial, Middle-income neighborhoods, and rich neighborhoods), we need 20–40 sample area data in total. If you have a colleague who can map these sample areas in GIS, please provide a shapefile of the sample areas to me. If not, just draw lines on a paper map, scan it as a high-resolution PDF, and send it to me. I will digitize the sample areas.

(2) In relation to (1), we need to have local staff who can verify an ML-predicted result to adjust the model.
The below image show examples of the sample areas gathered for the Niamey study:

![Sample areas](https://user-images.githubusercontent.com/64405484/149363357-ac2fe7d9-4aca-4345-88a1-c5d2f9e304a5.png)

### 1.2. Actual slumML analysis - STEP1 and STEP2
The original codes were developed by Alex Chunet.
Perform STEP 1 to generate morphological indices of the target building footprint layer. Then run STEP 2 to perform an automated supervised ML analysis.

## 2. Auxiliary materials
### 2.1. GOB2FC (Google Open Building layer to ESRI feature class)
This script is to convert the CSV file(s) of [Google Open Buildings](https://sites.research.google/open-buildings/) to a Feature Class.

![Layout2](https://user-images.githubusercontent.com/64405484/137813865-0abd8f0c-ff15-4980-9251-042a8f9dc66b.png)
An example map rendered in ArcGIS Pro (Cairo Metropolitan Area)

#### 2.2.1. How to use
This script uses ArcPy modules, so your environment should have ArcPy library. Simply, load the script to your Tool Box on your ArcGIS Pro project and run it. The target Open Buildings CSV file must be stored in the folder where the script is located.

If you want to test the script with a small chunk of a full CSV, modify the code:

```python
df_test = df_conf.iloc[0:100, :].copy()
df_test.reset_index(inplace=True, drop=True)

for i, r in df_conf.iterrows():
```
For example, iloc[0:100] will retirieve the first 100 records from the original data. df_conf should be replaced by df_test.

#### 2.2.2. NOTE

* Each CSV file based on [S2 geometry cells](https://s2geometry.io/) can contain a huge amount of geometries (+10 million), so it is highly recommended to limit the geographical scope of your CSV file. This [download region polygons](https://colab.research.google.com/github/google-research/google-research/blob/master/building_detection/open_buildings_download_region_polygons.ipynb#scrollTo=fwxfj3B1qUWu) tool developed by the Open Buildings Google team will help you to define the target geographical extent when you download the CSV file.
* Process speed: Approximately **0.5 million geometries / about 5 hours** with Windows 10 - AMD Ryzen 9 3900X 12-Core Processor 3.79 GHz, 32GB RAM.
* The data could contain invalid geometries (basically 'EMPTY' geometries). These invalid geometries will be automatically removed from the resulted feature class.
