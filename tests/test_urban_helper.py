"""Unit tests for the urban_helper.py module"""
import pytest  # noqa: F401
from GOSTurban import urban_helper
import os
import shutil
import numpy as np
from unittest import mock
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from unittest.mock import MagicMock


class TestSummarizePopulation:
    """Tests for the summarize_population class."""

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
                return raster

        return_val = tmpOutput()
        return return_val

    def mocked_zonal_stats(self, inr, minVal=0):
        """Mocking the gostrocks zonalstats function."""
        return np.ones((1, 4))

    @mock.patch("rasterio.open", mocked_rasterio_open)
    def test_01(self, tmp_path):
        # make the admin layer gpd
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
        admin_layer = gpd.GeoDataFrame(df, geometry=df.geometry, crs="EPSG:3857")
        # try to initialize the class
        sp = urban_helper.summarize_population(
            "pop_path.tif", admin_layer, temp_folder=tmp_path
        )
        assert isinstance(sp, urban_helper.summarize_population)
        assert isinstance(sp.admin_layer, gpd.GeoDataFrame)
        assert isinstance(sp.urban_layer, str)

        # check the inputs - they don't exist so check value will be False
        cv = sp.check_inputs()
        assert isinstance(cv, bool)
        assert cv is False
        assert isinstance(sp.check_vals, dict)

    @mock.patch("rasterio.open", mocked_rasterio_open)
    def test_02(self, tmp_path):
        # make the admin layer gpd
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
        admin_layer = gpd.GeoDataFrame(df, geometry=df.geometry, crs="EPSG:3857")
        # try to initialize the class
        sp = urban_helper.summarize_population("fake_dir/pop_path.tif", admin_layer)
        assert sp.temp_folder == "fake_dir"

    def test_03(self, tmp_path):
        # make the admin layer gpd
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
        admin_layer = gpd.GeoDataFrame(df, geometry=df.geometry, crs="EPSG:3857")
        # copy tutorial data over into the tmp folder
        shutil.copyfile(
            os.path.join(".", "data", "tutorial_data", "wp_2020_1k_AOI.tif"),
            os.path.join(tmp_path, "pop_path.tif"),
        )
        shutil.copyfile(
            os.path.join(".", "data", "tutorial_data", "wp_2020_1k_AOI.tif"),
            os.path.join(tmp_path, "pop_path_urban.tif"),
        )
        shutil.copyfile(
            os.path.join(".", "data", "tutorial_data", "wp_2020_1k_AOI.tif"),
            os.path.join(tmp_path, "pop_path_urban_hd.tif"),
        )

        # try to initialize the class
        sp = urban_helper.summarize_population(
            os.path.join(tmp_path, "pop_path.tif"), admin_layer, temp_folder=tmp_path
        )

        # calculate zonal
        zdf = sp.calculate_zonal()
        # assertions
        assert isinstance(zdf, pd.DataFrame)
        assert zdf.shape[1] == 12


class TestUrbanCountry:
    """Tests for the urban_country class."""

    def mocked_elevation_clip(
        bounds=None, max_download_tiles=None, output=None, product=None
    ):
        """Mocked version of elevation.clip()"""
        return MagicMock()

    @mock.patch("elevation.clip", mocked_elevation_clip)
    def test_init(self, tmp_path):
        # put USA_adm.shp in the tmp_path
        with open(tmp_path / "usa_adm.shp", "w") as f:
            f.write("fake shapefile")
        # make the class
        uc = urban_helper.urban_country(
            iso3="USA",
            output_folder=tmp_path,
            country_bounds="data/tutorial_data/AOI.geojson",
            pop_files=[],
            final_folder=tmp_path,
        )
        assert uc.iso3 == "USA"

        # change the uc.inD object
        uc.inD = MagicMock()

        # process the dem
        uc.process_dem()
        # doesn't return anything or change any attributes so nothing to assert

    def test_init_02(self, tmp_path):
        outf = os.path.join(tmp_path, "fin_folder")
        os.makedirs(outf)
        os.makedirs(os.path.join(outf, "FINAL_STANDARD"))
        admin_pth = os.path.join(outf, "FINAL_STANDARD", "usa_adm.shp")
        with open(admin_pth, "w") as f:
            f.write("fake shapefile")

        uc = urban_helper.urban_country(
            iso3="USA",
            output_folder=outf,
            country_bounds=[],
            pop_files=[],
        )
        # minor assertions about class attributes
        assert uc.admin_shp == admin_pth
        assert isinstance(uc.pop_files, list)
