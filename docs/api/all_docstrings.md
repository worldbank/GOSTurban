# GOSTurban API Docstrings

## LEI

### `_mp_lei(curRxx, transformxx, idx_xx, old_list=[4, 5, 6], new_list=[3], buffer_dist=300)`

**Description:**

calculate and summarize LEI for curRxx, designed for use in multiprocessing function

---

### `lei_from_feature(inD, inR, old_list, new_list, buffer_dist=300, measure_crs=None, idx_col=None, verbose=False)`

**Description:**

Calculate the Landscape Expansion Index (LEI) from a categorical dataset
for each polygonal feature in inD

**Parameters:**

- `inD` (*geopands.GeoDataFrame*): Feature dataset for which to calculate LEI.
- `inR` (*rasterio.DatasetReader*): Raster of built area evolution data.
- `old_list` (*list*, optional): values in inR to be considered baseline (or t0).
- `new_list` (*list*, optional): values in inR to be considered new urban areas.
- `buffer_dist` (*int*, optional): distance to search around the newly developed area from which to search for existing built area, by default 300.
- `measure_crs` (*int*, optional): CRS number to use for measurement, by default None.
- `idx_col` (*str*, optional): Column name to use as index, by default None.
- `verbose` (*bool*, optional): Whether to print progress messages, by default False.

**Returns:**

- `pandas.DataFrame`: DataFrame containing the LEI results.

---

### `calculate_LEI(inputGHSL, old_list, new_list, buffer_dist=300, transform='')`

**Description:**

Calculate Landscape Expansion Index (LEI) through comparison of categorical values in a single raster dataset.

**Parameters:**

- `inputGHSL` (*str or rasterio.DatasetRaster or numpy.array*): Landcover dataset containing categorical values.
- `old_list` (*list of integers*): values in inputGHSL to be considered baseline (or t0).
- `new_list` (*list of integers*): Values in inputGHSL to be considered new urban areas.
- `buffer_dist` (*int*, optional): Distance to search around the newly developed area from which to search for existing built area, by default 300.
- `transform` (*str*, optional): Raster transform information, by default "".

**Returns:**

- `array of [curShape, oldArea, totalArea]`: results for each new urban area found in the dataset; curShape is the geometry of the new urban area, oldArea is the amount of old urban area found within buffer_dist of the new area, totalArea is the total area within buffer_dist of the new area.

---

### `summarize_LEI(in_file, leap_val=0.05, exp_val=0.9)`

**Description:**

Summarize the LEI results produced by self.calculate_LEI

**Parameters:**

- `in_file` (*string path or pandas.DataFrame*): LEI results generated from calculate_LEI above.
- `leap_val` (*float*, optional): LEI value below which areas are considered to be leapfrog, defaults to 0.05.
- `exp_val` (*float*, optional): LEI value above which areas are considered to be infill, defaults to 0.9.

**Returns:**

- `pd.DataFrame`: pandas groupby row summarizing area in m2 of leapfrog, expansion, and infill areas.

---

## UrbanRaster

### `summarize_urban_pop(inD, urbanLyr, pop_lyr, reproj=True, calc_pop=True)`

**Description:**

Summarize population and urban population within the defined polygonal dataset (inD)

**Parameters:**

- `inD` (*gpd.GeoDataFrame*): Input polygon dataset to summarize population within.
- `urbanLyr` (*rasterio.DatasetReader*): Rasterio object representing urban extent raster as binary values.
- `pop_lyr` (*rasterio.DatasetReader*): Rasterio object representing population raster to summarize.

---

### `geocode_cities(urban_extents)`

**Description:**

Generate names for polygon urban extents

**Parameters:**

- `urban_extents`: geopandas dataframe of polygons to be named. Need to be in epsg:4326.

---

### `urbanGriddedPop.__init__(inRaster)`

**Description:**

Create urban definitions using gridded population data.

**Parameters:**

- `inRaster`: string or rasterio object representing gridded population data.

---

### `urbanGriddedPop.calculateDegurba(urbDens=300, hdDens=1500, urbThresh=5000, hdThresh=50000, minPopThresh=50, out_raster='', print_message='', verbose=False)`

**Description:**

Calculate complete DEGURBA classification based on gridded population data
([GHSL DEGURBA definitions](https://ghsl.jrc.ec.europa.eu/degurbaDefinitions.php))
CLASSES:
(30) Urban centre - dens: 1500, totalpop: 50000, smoothed
(23) Urban cluster, town, dense urban cluster - dens: 1500, totalpop: >5000, <50000, not type 30
(22) Urban cluster, town, semidense urban cluster - dens: 300, totalpop: >5000, farther than 3 km from 23 or another 22
(21) Urban cluster, suburb - dens: >300, totalpop: >5000, within 3km of 23 or 22
(13) Rural, village  - dens: >300, totalpop: >500, <5000
(12) Rural, dispersed, low density - dens: >50,
(11) Rural, dispersed, low density - the rest that are populated

**Parameters:**

- `urbDens`: integer of the minimum density value to be counted as urban.
- `hdDens`: integer of the minimum density value to be counted as high density.
- `urbThresh`: integer minimum total settlement population to be considered urban.
- `hdThresh`: integer minimum total settlement population to be considered high density.

---

### `urbanGriddedPop.calculateUrban(densVal=300, totalPopThresh=5000, smooth=False, verbose=False, queen=False, raster='', raster_pop='', print_message='', sieve=False)`

**Description:**

Generate urban extents from gridded population data through the application of a minimum
density threshold and a minimum total population threshold

**Parameters:**

- `densVal` (*int*, optional): Minimum density value to be counted as urban, by default 300.
- `totalPopThresh` (*int*, optional): Minimum total settlement population to be considered urban, by default 5000.
- `smooth` (*bool*, optional): Whether to run a single modal smoothing function, by default False.
- `verbose` (*bool*, optional): Whether to print progress messages, by default False.
- `queen` (*bool*, optional): Whether to dissolve final shape to connect queen's contiguity, by default False.
- `raster` (*str*, optional): Path to create a boolean raster of urban and not, by default "".
- `raster_pop` (*str*, optional): Path to create a raster of the population layer only in the urban areas, by default "".
- `print_message` (*str*, optional): Message to print during processing, by default "".
- `sieve` (*bool*, optional): Whether to apply a sieve filter to the urban raster, by default False.

**Returns:**

- `gpd.GeoDataFrame`: GeoDataFrame of the urban extents.

---
