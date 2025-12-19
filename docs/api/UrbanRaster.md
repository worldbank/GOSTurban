# UrbanRaster

## `summarize_urban_pop(inD, urbanLyr, pop_lyr, reproj=True, calc_pop=True)`

**Description:**

Summarize population and urban population within the defined polygonal dataset (inD)

**Parameters:**

- `inD` (*gpd.GeoDataFrame*): Input polygon dataset to summarize population within.
- `urbanLyr` (*rasterio.DatasetReader*): Rasterio object representing urban extent raster as binary values.
- `pop_lyr` (*rasterio.DatasetReader*): Rasterio object representing population raster to summarize.

---

## `geocode_cities(urban_extents)`

**Description:**

Generate names for polygon urban extents

**Parameters:**

- `urban_extents`: geopandas dataframe of polygons to be named. Need to be in epsg:4326.

---

## `urbanGriddedPop.__init__(inRaster)`

**Description:**

Create urban definitions using gridded population data.

**Parameters:**

- `inRaster`: string or rasterio object representing gridded population data.

---

## `urbanGriddedPop.calculateDegurba(urbDens=300, hdDens=1500, urbThresh=5000, hdThresh=50000, minPopThresh=50, out_raster='', print_message='', verbose=False)`

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

## `urbanGriddedPop.calculateUrban(densVal=300, totalPopThresh=5000, smooth=False, verbose=False, queen=False, raster='', raster_pop='', print_message='', sieve=False)`

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
