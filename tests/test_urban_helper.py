"""Unit tests for the urban_helper.py module"""
import pytest  # noqa: F401
from GOSTurban import urban_helper


class TestUrbanCountry:
    """Tests for the urban_country class."""

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
