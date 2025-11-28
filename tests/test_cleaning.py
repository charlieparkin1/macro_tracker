import unittest
import pandas as pd
from src.processing.cleaners import normalise_series


class TestCleaners(unittest.TestCase):
    def test_normalise_series_basic(self):
        # 1. Create dummy raw data
        raw_data = {"date": ["2023-01-01", "2023-02-01"], "value": [100.5, 101.0]}
        df = pd.DataFrame(raw_data)

        # 2. Run the function
        result = normalise_series(df, "FRED", "Test Indicator")

        # 3. Assertions (The Test)
        self.assertFalse(result.empty)
        self.assertEqual(len(result), 2)
        self.assertIn("source", result.columns)
        self.assertEqual(result.iloc[0]["source"], "FRED")
        self.assertEqual(result.iloc[0]["indicator"], "Test Indicator")

    def test_handle_empty_data(self):
        # Test how it handles empty input
        df = pd.DataFrame()
        result = normalise_series(df, "FRED", "Empty Test")
        self.assertTrue(result.empty)
        self.assertIn("date", result.columns)  # Schema should still exist


if __name__ == "__main__":
    unittest.main()
