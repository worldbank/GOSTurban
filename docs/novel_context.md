# Novel Urbanization
The World Bank has long been interested in identifying novel methods for quantifying urbanization; relying on countries' reported statistics belies the inherent differences in how countries calculate urban areas, and makes comparisons across space and time very difficult. 

This project compares two urbanization methods (Degree of Urbanization and Dartboard) across sub-saharan Africa, including the effects on poverty measures in a select number of countries. Details on the methods can be found below. If you want to access the data, see links below:

- [Map comparing the results](https://geowb.maps.arcgis.com/apps/Compare/index.html?appid=c1cb50e173e54c58b4770b7db8ea1c65) of the two urbanization methods.
- [Download the data](https://datacatalog.worldbank.org/int/search/dataset/0060818/Novel-urbanization---urban-extents) from the World Bank's Development Data Catalog.

## [Degree of Urbanization](https://ghsl.jrc.ec.europa.eu/degurbaOverview.php)

The European Commission developed a globally consistent, people-centric definition of urban areas. The basic approach is to apply a threshold to population grids on both the minimum population density, and then on the minimum total population of the resulting settlements. While the team at the EC continues to advance and iterate on their methodology, we rely on the original definitions of urban they produced:

| Urban area | Min Pop Density | Min Settlement Pop |
| --- | --- | --- |
| Urban areas | 300 people/km2 | 5000 people |
| High density urban areas | 1500 people/km2 | 50000 people |

## [Dartboard](https://www.sciencedirect.com/science/article/pii/S0094119019301032)

This method eschews the absolute density thresholds of the EC methodology and instead compares actual building density to counterfactual density after random redistribution of the pixel values in its neighbourhood. The methodology is applied following these steps:

1. Computing a smoothed density of the variable on which the delineation is based (building density or population).
2. Randomly redistributing pixel values (3000 iterations) the variable values at the pixel level across all livable areas such that obtaining, for each pixel, a counterfactual distribution of the variable considered.
3. Classifying as urban those pixels for which the actual density is above the 95th percentile of the smoothed counterfactual distribution.
4. Grouping contiguous urban pixels to form urban areas
5. Then the random redistribution of pixels� values is repeated but within these Urban areas only, which gives a new counterfactual distribution. Contiguous pixels of urban areas for which actual density is above the 95th percentile of this within urban area new counterfactual distribution are classified as Cores. Urban areas that have at least one core are classified as Cities.

| Urban area | Definition |
| --- | --- |
| Urban areas | contiguous pixels for which the density is above the 95th percentile of the counterfactual |
| Cores | contiguous pixels within urban areas that are above the 95th percentile of the counterfactual within the urban core |
| Cities | urban areas that have a core |
