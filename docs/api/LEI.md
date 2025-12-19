# LEI

## `_mp_lei(curRxx, transformxx, idx_xx, old_list=[4, 5, 6], new_list=[3], buffer_dist=300)`

**Description:**

calculate and summarize LEI for curRxx, designed for use in multiprocessing function

---

## `lei_from_feature(inD, inR, old_list, new_list, buffer_dist=300, measure_crs=None, idx_col=None, verbose=False)`

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

## `calculate_LEI(inputGHSL, old_list, new_list, buffer_dist=300, transform='')`

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

## `summarize_LEI(in_file, leap_val=0.05, exp_val=0.9)`

**Description:**

Summarize the LEI results produced by self.calculate_LEI

**Parameters:**

- `in_file` (*string path or pandas.DataFrame*): LEI results generated from calculate_LEI above.
- `leap_val` (*float*, optional): LEI value below which areas are considered to be leapfrog, defaults to 0.05.
- `exp_val` (*float*, optional): LEI value above which areas are considered to be infill, defaults to 0.9.

**Returns:**

- `pd.DataFrame`: pandas groupby row summarizing area in m2 of leapfrog, expansion, and infill areas.

---
