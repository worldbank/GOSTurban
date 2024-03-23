"""Unit tests for the country_helper.py module"""
import pytest  # noqa: F401
from GOSTurban import country_helper
import GOSTurban.UrbanRaster as urban
import GOSTrocks.ntlMisc as ntl
import rasterio
import os
import GOSTrocks.rasterMisc as rMisc
from unittest.mock import MagicMock


class TestUrbanHelper:
    """Tests for the urban_county class."""

    # make some fake data to test with
    ch = country_helper.urban_country(
        iso3="USA", sel_country="United States", cur_folder="data", inP=[1, 2, 3]
    )

    def test_urban_helper(self):
        # assert things about the result
        assert self.ch.iso3 == "USA"
        assert self.ch.sel_country == "United States"
        assert self.ch.cur_folder == "data"
        assert self.ch.inP == [1, 2, 3]
        assert self.ch.urban_extents_file == os.path.join(
            "data", "USA_urban_extents.geojson"
        )
        assert self.ch.urban_ntl == os.path.join("data", "USA_urban_ntl.csv")

    def test_calculate_urban_extents(self, tmp_path):
        """Test the calculate_urban_extents method."""
        # make a tmp location for output
        out_folder = tmp_path / "output"
        # mock the urban.urbanGriddedPop function
        urban.urbanGriddedPop = MagicMock()
        # make the class
        ch = country_helper.urban_country(
            iso3="USA", sel_country="placeholder", cur_folder=out_folder, inP=[1, 2, 3]
        )
        # try calling the method
        ch.calculate_urban_extents()
        # assert that the function was called
        urban.urbanGriddedPop.assert_called_once_with(ch.inP)

    def test_summarize_ntl(self, tmp_path):
        """Test the summarize_ntl method."""
        # make a tmp location for output
        out_folder = tmp_path / "output"
        # make the class
        ch = country_helper.urban_country(
            iso3="USA", sel_country="placeholder", cur_folder=out_folder, inP=[1, 2, 3]
        )
        # mock some of the methods called
        ntl.aws_search_ntl = MagicMock()
        # try calling the method
        ch.summarize_ntl()
        # assert that the mocked function was called
        ntl.aws_search_ntl.assert_called_once()

    def test_summarize_ghsl(self, tmp_path):
        """Test the summarize_ghsl method."""
        # make a tmp location for output
        out_folder = tmp_path / "output"
        # make the class
        ch = country_helper.urban_country(
            iso3="USA", sel_country="placeholder", cur_folder=out_folder, inP=[1, 2, 3]
        )
        # mock rasterio.open
        rasterio.open = MagicMock()
        # mock zonalStats
        rMisc.zonalStats = MagicMock()
        # try calling the method
        ch.summarize_ghsl(ghsl_files=["a_a_a_e", "b_b_b_f"])
        # assert that the mocked functions were called
        rasterio.open.assert_called()
        rMisc.zonalStats.assert_called()

    def test_delete_urban_data(self, tmp_path):
        """Test the delete_urban_data method."""
        # make a tmp location for output
        out_folder = tmp_path / "output"
        # make the class
        ch = country_helper.urban_country(
            iso3="USA", sel_country="placeholder", cur_folder=out_folder, inP=[1, 2, 3]
        )
        # make expected files
        with open(ch.urban_extents_file, "w") as f:
            f.write("test")
        with open(ch.urban_extents_raster_file, "w") as f:
            f.write("test")
        with open(ch.urban_extents_hd_file, "w") as f:
            f.write("test")
        with open(ch.urban_extents_hd_raster_file, "w") as f:
            f.write("test")
        # assert the files exist
        assert os.path.exists(ch.urban_extents_file)
        assert os.path.exists(ch.urban_extents_raster_file)
        assert os.path.exists(ch.urban_extents_hd_file)
        assert os.path.exists(ch.urban_extents_hd_raster_file)
        # try calling the method
        ch.delete_urban_data()
        # assert the files are deleted
        assert not os.path.exists(ch.urban_extents_file)
        assert not os.path.exists(ch.urban_extents_raster_file)
        assert not os.path.exists(ch.urban_extents_hd_file)
        assert not os.path.exists(ch.urban_extents_hd_raster_file)
