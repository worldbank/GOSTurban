"""Unit tests for the country_helper.py module"""
import pytest  # noqa: F401
from GOSTurban import country_helper
import GOSTurban.UrbanRaster as urban
import GOSTrocks.ntlMisc as ntl
import rasterio
import os
import GOSTrocks.rasterMisc as rMisc
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest import mock
import numpy as np


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

    def test_summarize_ntl_list_err(self, tmp_path, capfd):
        """Test the summarize_ntl method with an ntl list, erroring."""
        # make a tmp location for output
        out_folder = tmp_path / "output"
        # make the class
        ch = country_helper.urban_country(
            iso3="USA", sel_country="placeholder", cur_folder=out_folder, inP=[1, 2, 3]
        )
        # mock some of the methods called
        ntl.aws_search_ntl = MagicMock()
        # try calling the method
        ch.summarize_ntl(ntl_files=["invalid01", "invalid02"])
        # captured output
        captured = capfd.readouterr()
        assert captured.out.split("\t")[1][0] == "*"
        assert captured.out.split("\t")[2][0] == "*"

    def test_summarize_ntl_list(self, tmp_path, capfd):
        """Test the summarize_ntl method with an ntl list, erroring."""
        # make a tmp location for output
        out_folder = tmp_path / "output"
        # make the class
        ch = country_helper.urban_country(
            iso3="USA", sel_country="placeholder", cur_folder=out_folder, inP=[1, 2, 3]
        )
        # mock some of the methods called
        ntl.aws_search_ntl = MagicMock()
        rasterio.open = MagicMock()
        # try calling the method
        ch.summarize_ntl(ntl_files=["a_b_c"])
        # captured output
        captured = capfd.readouterr()
        assert len(captured.out.split("\t")) > 1

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

    def test_summarize_ghsl02(self, tmp_path):
        """Test the summarize_ghsl method with clip_raster=True."""
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
        # mock the clipraster function
        rMisc.clipRaster = MagicMock()
        # try calling the method
        ch.summarize_ghsl(ghsl_files=["a_a_a_e", "b_b_b_f"], clip_raster=True)
        # assert that the mocked functions were called
        rasterio.open.assert_called()
        rMisc.zonalStats.assert_called()
        rMisc.clipRaster.assert_called()

    def mocked_rasterio_open(self, t="w"):
        """Mocked function for rasterio.open()"""

        class tmpOutput:
            def __init__(self):
                self.crs = "EPSG:4326"
                self.meta = MagicMock()

            def read(self):
                raster = np.zeros((10, 10))
                raster[:5, :5] = 1500
                raster[5:, 5:] = 3
                return raster

        return_val = tmpOutput()
        return return_val

    @mock.patch("rasterio.open", mocked_rasterio_open)
    def test_summarize_ghsl03(self, tmp_path):
        """Test the summarize_ghsl method with binary_calc=True.
        Have not clipped local ghsl data so will throw error."""
        # make a tmp location for output
        out_folder = tmp_path / "output"
        # make the class
        ch = country_helper.urban_country(
            iso3="USA", sel_country="placeholder", cur_folder=out_folder, inP=[1, 2, 3]
        )
        # mock zonalStats
        rMisc.zonalStats = MagicMock()
        # try calling the method expecting the value error
        with pytest.raises(ValueError):
            ch.summarize_ghsl(ghsl_files=["a_a_a_e", "b_b_b_f"], binary_calc=True)

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

    def test_delete_urban_data_exception(self, tmp_path):
        """Test the delete_urban_data method's exception."""
        # make a tmp location for output
        out_folder = tmp_path / "output"
        # make the class
        ch = country_helper.urban_country(
            iso3="USA", sel_country="placeholder", cur_folder=out_folder, inP=[1, 2, 3]
        )
        # don't make any files and call the method
        ch.delete_urban_data()
        # it should have used the exception and invoked "pass" for the loop

    def test_urban_country_inP_str(self):
        """Testing with string input for inP."""
        with patch("rasterio.open") as mock_open:
            mock_open = MagicMock()  # noqa
            ch = country_helper.urban_country(
                iso3="USA", sel_country="United States", cur_folder="data", inP="str"
            )
            # assert that the mocked open was used
            assert isinstance(ch.inP, MagicMock)
