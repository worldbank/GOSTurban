"""Unit tests for the LEI.py module"""
import pytest  # noqa: F401
from unittest import mock
from GOSTurban import LEI
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from unittest.mock import MagicMock
import numpy as np


class TestCalculateLEI:
    """Tests for the calculate_LEI() function."""

    # make some fake data to test with
    raster = np.zeros((10, 10))
    raster[:5, :5] = 4
    raster[5:, 5:] = 3

    def test_calculate_lei(self):
        # run the function
        result = LEI.calculate_LEI(
            self.raster,
            old_list=[4],
            new_list=[3],
            buffer_dist=1,
            transform=(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
        )
        # assert things about the result
        assert isinstance(result, list)

    def mocked_rasterio_open(self):
        """Mocked function for rasterio.open()"""

        class tmpOutput:
            def __init__(self):
                self.transform = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

            def read(self):
                raster = np.zeros((10, 10))
                raster[:5, :5] = 4
                raster[5:, 5:] = 3
                return raster

        return_val = tmpOutput()
        return return_val

    @mock.patch("rasterio.open", mocked_rasterio_open)
    def test_calculate_lei_rasterio(self):
        # run the function
        result = LEI.calculate_LEI(
            "str input",
            old_list=[4],
            new_list=[3],
            buffer_dist=1,
            transform=(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
        )
        # assert things about the result
        assert isinstance(result, list)


class TestSummarizeLEI:
    """Tests for the summarize_LEI() function."""

    # make some fake data to test with
    df = pd.DataFrame(
        {
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 1)]),
                Polygon([(0, 0), (1, 0), (1, 1)]),
                Polygon([(0, 0), (1, 0), (1, 1)]),
            ],
            "LEI": [0.5, 0.6, 0.7],
        }
    )

    def test_summarize_lei(self):
        # run the function
        result = LEI.summarize_LEI(self.df)
        # assert things about the result
        assert isinstance(result, pd.Series)
        assert result.name == "area"

    def mocked_pd_read_csv(self):
        """Mock the pandas read_csv function."""
        df = pd.DataFrame(
            {
                "geometry": [
                    "Polygon((0 0, 1 0, 1 1, 0 0))",
                    "Polygon((0 0, 1 0, 1 1, 0 0))",
                    "Polygon((0 0, 1 0, 1 1, 0 0))",
                ],
                "LEI": [0.5, 0.6, 0.7],
            }
        )
        return df

    @mock.patch("pandas.read_csv", mocked_pd_read_csv)
    def test_summarize_lei_str(self):
        # testing the function with a string input
        result = LEI.summarize_LEI("str")
        # assert things about the result
        assert isinstance(result, pd.Series)
        assert result.name == "area"

    def test_mp_lei(self):
        # mock the calculate_LEI function
        LEI.calculate_LEI = MagicMock(
            return_value=[
                (Polygon(), 1, 2),
                (Polygon(), 3, 4),
                (Polygon(), 5, 6),
                (Polygon(), 7, 8),
                (Polygon(), 9, 10),
                (Polygon(), 11, 12),
                (Polygon(), 13, 14),
                (Polygon(), 15, 16),
                (Polygon(), 17, 18),
            ]
        )
        # run the function
        result = LEI.mp_lei(
            curRxx=None,
            transformxx=None,
            idx_xx=0,
            old_list=[4, 5, 6],
            new_list=[3],
            buffer_dist=300,
        )
        # assert things about the result
        assert isinstance(result, pd.Series)
        assert result.name == "area"


class TestCalculateLEIClass:
    """Tests for the calculate_LEI_class() function."""

    def test_calculate_lei_class_01(self):
        val = LEI.calculate_LEI_class(0.1, 1.0, 2.0)
        assert val == "Leapfrog"

    def test_calculate_lei_class_02(self):
        val = LEI.calculate_LEI_class(1.5, 1.0, 2.0)
        assert val == "Expansion"

    def test_calculate_lei_class_03(self):
        val = LEI.calculate_LEI_class(2.5, 1.0, 2.0)
        assert val == "Infill"


class TestLEIFromFeature:
    """Tests for the lei_from_feature() function."""

    # make some fake data to use for tests
    df = pd.DataFrame(
        {
            "idx": ["a", "b", "c"],
            "geometry": [
                Polygon([(0, 0), (1, 0), (1, 1)]),
                Polygon([(0, 0), (1, 0), (1, 1)]),
                Polygon([(0, 0), (1, 0), (1, 1)]),
            ],
        }
    )
    gdf = gpd.GeoDataFrame(df, geometry=df.geometry, crs="EPSG:3857")

    mocked_raster = MagicMock()
    mocked_raster.crs = "EPSG:4326"

    def mock_index(self, band):
        return np.array([1, 2, 3])

    mocked_raster.index = mock_index

    def mock_read(self, window=None):
        raster = np.zeros((10, 10))
        raster[:5, :5] = 4
        raster[5:, 5:] = 3
        return raster

    mocked_raster.read = mock_read

    def test_function(self):
        """Call function w/ default parameters."""
        result = LEI.lei_from_feature(self.gdf, self.mocked_raster)
        # assertions about output
        assert isinstance(result, pd.DataFrame)
        assert result.index.tolist() == result.idx.tolist()

    def test_function_measure_crs(self):
        """Call function defining measure_crs."""
        result = LEI.lei_from_feature(
            self.gdf, self.mocked_raster, measure_crs="ESRI:54009"
        )
        # assertions about output
        assert isinstance(result, pd.DataFrame)
        assert result.index.tolist() == result.idx.tolist()

    def test_function_idx_col(self):
        """Call function defining idx_col."""
        result = LEI.lei_from_feature(self.gdf, self.mocked_raster, idx_col="idx")
        # assertions about output
        assert isinstance(result, pd.DataFrame)
        assert result.index.tolist() == result.idx.tolist()
