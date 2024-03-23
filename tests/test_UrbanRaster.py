"""Unit tests for the UrbanRaster.py module"""
import pytest  # noqa: F401
import geopandas as gpd
from GOSTurban import UrbanRaster


class TestGeocodeCities:
    """Tests for the geocode_cities() function."""

    def test_geocode_cities(self):
        # read some of the tutorial data to test
        gdf = gpd.read_file("data/tutorial_data/AOI.geojson")
        # run the function - adding city/state/country info
        result = UrbanRaster.geocode_cities(gdf)
        # assert things about the result
        # e.g., should have city/state/country columns
        assert "City" in result.columns
        assert "State" in result.columns
        assert "Country" in result.columns
