import tempfile
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from src.inference import predict_batch
from src.model import build_model, candidate_specs, predict_nonnegative, signed_log1p, validate_features
from src.retail import FEATURES, candidate_sales, make_features, make_snapshot


class ModelContracts(unittest.TestCase):
    def test_signed_log(self):
        actual = signed_log1p(np.array([-100, 0, 100]))
        np.testing.assert_allclose(actual, [-np.log(101), 0, np.log(101)])

    def test_invalid_features_fail(self):
        with self.assertRaises(ValueError):
            validate_features(pd.DataFrame({"recency_days": [1]}))
        x = pd.DataFrame(np.zeros((1, len(FEATURES))), columns=FEATURES)
        x.iloc[0, 0] = np.inf
        with self.assertRaises(ValueError):
            validate_features(x)

    def test_serialization_predictions_and_column_order(self):
        rng = np.random.default_rng(42)
        x = pd.DataFrame(rng.uniform(0, 5, (30, len(FEATURES))), columns=FEATURES)
        model = build_model(candidate_specs()[0]).fit(x, rng.uniform(0, 100, 30))
        expected = predict_nonnegative(model, x)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.joblib"
            joblib.dump(model, path)
            actual = predict_nonnegative(joblib.load(path), x[FEATURES[::-1]])
        np.testing.assert_allclose(expected, actual)
        self.assertTrue((actual >= 0).all())

    def test_training_inference_feature_parity(self):
        t = pd.Timestamp("2011-11-01")
        start = t - pd.Timedelta(days=90)
        sales = pd.DataFrame([["a", "1", "p", start, 1, 10.0],
                              ["a", "2", "p", t, 1, 50.0]],
                             columns=["CustomerID", "InvoiceNo", "StockCode", "InvoiceDate", "Quantity", "value_gbp"])
        batch = make_features(sales, t, start)
        training = make_snapshot(sales, t, start, t + pd.Timedelta(days=30))
        assert_frame_equal(batch[["CustomerID"] + FEATURES], training[["CustomerID"] + FEATURES])

    def test_inference_does_not_need_future_response(self):
        t = pd.Timestamp("2011-11-01")
        raw = pd.DataFrame([["a", "1", "p", t - pd.Timedelta(days=90), 1, 10.0],
                            ["a", "2", "p", t - pd.Timedelta(days=1), 1, 20.0]],
                           columns=["CustomerID", "InvoiceNo", "StockCode", "InvoiceDate", "Quantity", "UnitPrice"])
        for col in ("CustomerID", "InvoiceNo", "StockCode"):
            raw[col] = raw[col].astype("string")
        x = make_features(candidate_sales(raw), t, raw.InvoiceDate.min())
        model = build_model(candidate_specs()[0]).fit(x[FEATURES], [30])
        bundle = {"model": model, "selection": {"test_reference": "2011-11-01", "selected": {"id": "test"}}}
        out = predict_batch(raw, bundle, t, observed_through=t)
        self.assertEqual(len(out), 1)
        self.assertEqual(out.prediction_gbp.iloc[0], 10)
        with self.assertRaises(ValueError):
            predict_batch(raw, bundle, t + pd.Timedelta(days=1), observed_through=t)


if __name__ == "__main__":
    unittest.main()
