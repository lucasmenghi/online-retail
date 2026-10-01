"""Comparação inicial, sem busca de hiperparâmetros e sem uso do teste final."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge, TweedieRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from src.retail import FEATURES, RESPONSE, temporal_fold


def metrics(y, prediction):
    y, prediction = np.asarray(y, float), np.asarray(prediction, float)
    if not np.isfinite(prediction).all():
        raise ValueError("Previsões não finitas")
    error = prediction - y
    return {"n": len(y), "rmse_gbp": np.sqrt(np.mean(error ** 2)),
            "mae_gbp": np.mean(np.abs(error)), "bias_gbp": np.mean(error),
            "observed_total_gbp": y.sum(), "predicted_total_gbp": prediction.sum(),
            "total_bias_pct": 100 * error.sum() / y.sum() if y.sum() else np.nan}


def evaluate_development(table):
    rows, predictions = [], []
    references = sorted(table.reference_date.unique())[3:]
    for reference in references:
        train, validation = temporal_fold(table, reference)
        estimates = {
            "zero": np.zeros(len(validation)),
            "train_mean": np.full(len(validation), train[RESPONSE].mean()),
            "last_30d": validation.spend_30d.to_numpy(),
            "last_90d_div3": validation.spend_90d.to_numpy() / 3,
        }
        models = {
            "ridge": make_pipeline(StandardScaler(), Ridge(alpha=100)),
            "tweedie": make_pipeline(StandardScaler(), TweedieRegressor(power=1.5, alpha=10, max_iter=2000)),
            # Evita validação aleatória interna; iterações fixadas antes dos resultados.
            "hist_gradient_boosting": HistGradientBoostingRegressor(
                max_iter=150, max_leaf_nodes=15, min_samples_leaf=30,
                l2_regularization=10, early_stopping=False, random_state=42),
        }
        with threadpool_limits(limits=2):
            for name, model in models.items():
                model.fit(train[FEATURES], train[RESPONSE])
                estimates[name] = model.predict(validation[FEATURES])
        for name, values in estimates.items():
            negative_n = int((np.asarray(values) < 0).sum())
            values = np.maximum(values, 0)  # Restrição monetária explícita; reporta incidência.
            rows.append({"model": name, "reference_date": pd.Timestamp(reference),
                         "train_n": len(train), "train_response_end": train.response_end.max(),
                         "negative_predictions_clipped": negative_n,
                         **metrics(validation[RESPONSE], values)})
            pred = validation[["CustomerID", "reference_date", RESPONSE, "spend_90d"]].copy()
            pred["model"] = name
            pred["prediction"] = values
            predictions.append(pred)
    if not rows:
        raise ValueError("Referências insuficientes para backtest")
    detail, predictions = pd.DataFrame(rows), pd.concat(predictions, ignore_index=True)
    pooled = pd.DataFrame([{"model": name, **metrics(g[RESPONSE], g.prediction)}
                           for name, g in predictions.groupby("model")]).sort_values("rmse_gbp")
    # Totais pooled são soma de exposições cliente/referência, não receita contábil anual.
    return detail, pooled, predictions
