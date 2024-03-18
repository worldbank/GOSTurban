"""Unit tests for the country_helper.py module"""
import pytest  # noqa: F401
from GOSTurban import country_helper


class TestCountryHelper:
    """Tests for the CountryHelper class."""

    # make some fake data to test with
    ch = country_helper.urban_country(
        iso3="USA", sel_country="United States", cur_folder="data", inP=[1, 2, 3]
    )

    def test_country_helper(self):
        # assert things about the result
        assert self.ch.iso3 == "USA"
        assert self.ch.sel_country == "United States"
        assert self.ch.cur_folder == "data"
        assert self.ch.inP == [1, 2, 3]
