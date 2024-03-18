"""Unit tests for the LEI.py module"""
import pytest  # noqa: F401
from GOSTurban import LEI
import pandas as pd
from shapely.geometry import Polygon


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
