"""Estimadores reproduzíveis e contrato de inferência da versão v1."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge, TweedieRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from src.retail import FEATURES


def signed_log1p(values):
    """Reduz escala de features e preserva o sinal da tendência. Não transforma y."""
    x = np.asarray(values, dtype=float)
    return np.sign(x) * np.log1p(np.abs(x))


def candidate_specs():
    specs = []
    for transform in ("raw", "signed_log1p"):
        for alpha in (10, 100, 1000):
            specs.append({"id": f"ridge_{transform}_{alpha}", "family": "ridge",
                          "transform": transform, "alpha": alpha})
    for power in (1.2, 1.5, 1.8):
        for alpha in (0.1, 1, 10):
            specs.append({"id": f"tweedie_log_p{power}_a{alpha}", "family": "tweedie",
                          "transform": "signed_log1p", "power": power, "alpha": alpha})
    for loss in ("squared_error", "poisson"):
        for leaves in (7, 15):
            for l2 in (10, 100):
                specs.append({"id": f"hgb_{loss}_l{leaves}_r{l2}", "family": "hgb",
                              "loss": loss, "max_leaf_nodes": leaves,
                              "l2_regularization": l2, "max_iter": 200,
                              "min_samples_leaf": 40, "learning_rate": 0.1})
    return specs


def build_model(spec):
    if spec["family"] == "hgb":
        return HistGradientBoostingRegressor(
            **{k: spec[k] for k in ("loss", "max_leaf_nodes", "l2_regularization", "max_iter",
                                    "min_samples_leaf", "learning_rate")},
            early_stopping=False, random_state=42)
    steps = []
    if spec["transform"] == "signed_log1p":
        steps.append(FunctionTransformer(signed_log1p, validate=False))
    steps.append(StandardScaler())
    if spec["family"] == "ridge":
        steps.append(Ridge(alpha=spec["alpha"]))
    elif spec["family"] == "tweedie":
        steps.append(TweedieRegressor(power=spec["power"], alpha=spec["alpha"], max_iter=3000))
    else:
        raise ValueError(f"Família desconhecida: {spec['family']}")
    return make_pipeline(*steps)


def validate_features(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(FEATURES) - set(frame.columns)
    if missing:
        raise ValueError(f"Features ausentes: {sorted(missing)}")
    features = frame.loc[:, FEATURES].astype(float)
    if not np.isfinite(features.to_numpy()).all():
        raise ValueError("Features precisam ser finitas e sem nulos")
    nonnegative = [f for f in FEATURES if f != "spend_recent_vs_previous_30d"]
    if (features[nonnegative] < 0).any().any():
        raise ValueError("Feature não negativa contém valor negativo")
    return features


def predict_nonnegative(model, frame):
    features = validate_features(frame)
    if features.empty:
        return np.array([], dtype=float)
    predictions = np.asarray(model.predict(features), dtype=float)
    if not np.isfinite(predictions).all():
        raise ValueError("Modelo produziu previsão não finita")
    return np.maximum(predictions, 0)
