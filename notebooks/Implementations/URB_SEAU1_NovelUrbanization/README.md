# Novel Urbanization
The code herein support the extraction of the data and calculation of urban extents for the World Bank's experiment and investigation of two methods for evaluating urban.
- You can download the data [here](https://datacatalog.worldbank.org/int/search/dataset/0060818/Novel-urbanization---urban-extents)
- You can explore the urban extents [here in an online map](https://www.arcgis.com/apps/Compare/index.html?appid=c1cb50e173e54c58b4770b7db8ea1c65).

## [Degree of Urbanization](https://ghsl.jrc.ec.europa.eu/degurbaOverview.php)
The European Commission developed a globally consistent, people-centric definition of urban areas. The basic approach is to apply a threshold to population grids on both the minimum population density, and then on the minimum total population of the resulting settlements. While the team at the EC continues to advance and iterate on their methodology, we rely on the original definitions of urban they produced:

| Urban area | Min Pop Density | Min Settlement Pop |
| --- | --- | --- |
| Urban areas | 300 people/km2 | 5000 people |
| High density urban areas | 1500 people/km2 | 50000 people |

## [Bellefon (2021)](https://www.sciencedirect.com/science/article/pii/S0094119019301032)

This method eschews the absolute density thresholds of the EC methodology and instead compares actual building density to counterfactual density after random redistribution of the pixel values in its neighbourhood. The methodology is applied following these steps:
1.	Computing a smoothed density of the variable on which the delineation is based (building density or population).
2.	Randomly redistributing pixel values (3000 iterations) the variable values at the pixel level across all livable areas such that obtaining, for each pixel, a counterfactual distribution of the variable considered.
3.	Classifying as urban those pixels for which the actual density is above the 95th percentile of the smoothed counterfactual distribution.
4.	Grouping contiguous urban pixels to form urban areas
5.	Then the random redistribution of pixels’ values is repeated but within these Urban areas only, which gives a new counterfactual distribution. Contiguous pixels of urban areas for which actual density is above the 95th percentile of this within urban area new counterfactual distribution are classified as Cores. Urban areas that have at least one core are classified as Cities.

| Urban area | label | Definition |
| --- | --- | --- |
| Urban areas | __ur__ | contiguous pixels for which the density is above the 95th percentile of the counterfactual |
| Cores | __co__ | contiguous pixels within urban areas that are above the 95th percentile of the counterfactual within the urban core |
| Cities | __cc__ | urban areas that have a core |
| Pop centers | __ce__ | contiguous pixels within a city that are above the 95th percentile of the counterfactual within the city. |
