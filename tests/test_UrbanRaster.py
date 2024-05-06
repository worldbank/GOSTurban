"""Unit tests for the UrbanRaster.py module"""
import pytest  # noqa: F401
import geopandas as gpd
from GOSTurban import UrbanRaster
from unittest.mock import MagicMock
from unittest import mock
from unittest.mock import patch
import numpy as np


def test_tprint(capfd):
    """Test tprint function."""
    # call function
    UrbanRaster.tPrint("mymsg")
    # captured output
    captured = capfd.readouterr()
    assert captured.out.split("\t")[1][:5] == "mymsg"


class TestGeocodeCities:
    """Tests for the geocode_cities() function."""

    # read some of the tutorial data to test
    gdf = gpd.read_file("data/tutorial_data/AOI.geojson")

    def test_geocode_cities(self):
        gdf = self.gdf
        # run the function - adding city/state/country info
        result = UrbanRaster.geocode_cities(gdf)
        # assert things about the result
        # e.g., should have city/state/country columns
        assert "City" in result.columns
        assert "State" in result.columns
        assert "Country" in result.columns


class TestUrbanGriddedPop:
    """Testing the urban gridded population data class."""

    def mocked_rasterio_open(self, t="w"):
        """Mocked function for rasterio.open()"""

        class tmpOutput:
            def __init__(self):
                self.crs = "EPSG:4326"
                self.meta = MagicMock()

            def read(self):
                raster = np.zeros((10, 10))
                raster[:5, :5] = 4
                raster[5:, 5:] = 3
                raster = np.reshape(raster, [1, 10, 10])
                return raster

        return_val = tmpOutput()
        return return_val

    @mock.patch("rasterio.open", mocked_rasterio_open)
    def test_init_class(self):
        """Init with string that uses rasterio.open"""
        ugp = UrbanRaster.urbanGriddedPop("str")
        # assert known properties of the mocked object
        assert ugp.inR.crs == "EPSG:4326"

    def test_init_value_error(self):
        """Init with wrong type, raising a value error."""
        with pytest.raises(ValueError):
            UrbanRaster.urbanGriddedPop(5)

    @mock.patch("rasterio.open", mocked_rasterio_open)
    def test_burn_value(self):
        """Testing the private burn value function."""
        # make the object
        ugp = UrbanRaster.urbanGriddedPop("str")
        with patch("shapely.geometry") as mock_shape:
            mock_shape = {"type": "Point", "coordinates": [0, 1]}
            final_raster, allFeatures = ugp._burnValue(
                np.ones((5, 5), dtype=bool),
                1,
                np.zeros((5, 5)),
                [],
                "a",
                "pop",
                mock_shape,
            )
        # assertions
        assert final_raster.shape == (5, 5)
        assert final_raster[0, 0] == 0.0
        assert isinstance(allFeatures, list)
        assert len(allFeatures) == 1
        assert len(allFeatures[0]) == 4
        assert allFeatures[0][0] == "a"
