from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
 
long_description = "FUBAR"
 
setup(
    name='GOST_Urban',
    packages=['GOST_Urban'],
    install_requires=[
        'rasterio',
        'geopandas',
        'pandas',        
        'numpy',
        'scipy',
        'shapely',
        'geopy',
        'pyproj',
        'elevation',
        'richdem',
        'gostrocks',
        'geojson'        
    ],
    version='0.1.0',
    description='Multiple functions, tools, and tutorials for calculating urbanization based on gridded population data',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/worldbank/GOST_Urban",    
    author='Benjamin P. Stewart',    
    package_dir= {'':'src'}
)