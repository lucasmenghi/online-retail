import unittest
import pandas as pd
from pandas.testing import assert_frame_equal
from src.retail import FEATURES, RESPONSE, make_snapshot, temporal_fold


class TemporalContracts(unittest.TestCase):
    def setUp(self):
        self.t = pd.Timestamp("2011-06-01")
        self.start = self.t - pd.Timedelta(days=90)
        self.end = self.t + pd.Timedelta(days=30)
        self.sales = pd.DataFrame([
            ["a", "1", "x", self.start, 1, 10.0],
            ["a", "2", "x", self.t - pd.Timedelta(days=1), 2, 20.0],
            ["b", "3", "y", self.t - pd.Timedelta(days=2), 1, 5.0],
            ["a", "4", "x", self.t, 1, 40.0],
            ["a", "5", "x", self.end, 1, 999.0],
            ["new", "6", "x", self.t, 1, 100.0],
        ], columns=["CustomerID", "InvoiceNo", "StockCode", "InvoiceDate", "Quantity", "value_gbp"])

    def test_boundaries_population_and_zeros(self):
        s = make_snapshot(self.sales, self.t, self.start, self.end).set_index("CustomerID")
        self.assertEqual(set(s.index), {"a", "b"})
        self.assertEqual(s.loc["a", "spend_90d"], 30)
        self.assertEqual(s.loc["a", RESPONSE], 40)
        self.assertEqual(s.loc["b", RESPONSE], 0)

    def test_future_changes_cannot_change_features(self):
        original = make_snapshot(self.sales, self.t, self.start, self.end)
        altered = self.sales.copy()
        altered.loc[altered.InvoiceDate >= self.t, "value_gbp"] *= 100
        changed = make_snapshot(altered, self.t, self.start, self.end)
        assert_frame_equal(original[["CustomerID"] + FEATURES], changed[["CustomerID"] + FEATURES])

    def test_incomplete_response_is_not_zero(self):
        with self.assertRaises(ValueError):
            make_snapshot(self.sales, self.t, self.start, self.end - pd.Timedelta(days=1))

    def test_purge_overlapping_training_response(self):
        table = pd.DataFrame({"reference_date": pd.to_datetime(["2011-01-01", "2011-02-01", "2011-03-01"]),
                              "response_end": pd.to_datetime(["2011-01-31", "2011-03-03", "2011-03-31"])})
        train, valid = temporal_fold(table, pd.Timestamp("2011-03-01"))
        self.assertEqual(len(train), 1)
        self.assertLessEqual(train.response_end.max(), valid.reference_date.min())


if __name__ == "__main__":
    unittest.main()
