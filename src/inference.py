"""Inferência batch com paridade temporal e método recomendado explícito."""
import hashlib
from importlib.metadata import version
import json
from pathlib import Path

import joblib
import pandas as pd
from threadpoolctl import threadpool_limits

from src.model import predict_nonnegative
from src.retail import candidate_sales, make_features


def load_verified_bundle(artifact: Path, manifest_path: Path):
    """Carrega apenas o artefato local confiável cujo hash consta no manifesto."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if actual != manifest["sha256"]:
        raise ValueError("Hash do modelo diverge do manifesto; não carregar")
    bundle = joblib.load(artifact)
    for package, expected in bundle["selection"]["packages"].items():
        if version(package) != expected:
            raise ValueError(f"Versão incompatível: {package}; use {expected}")
    return bundle


def predict_batch(transactions, bundle, reference, *, observed_through=None):
    """O limite de cobertura é exclusivo; não é necessário ter a resposta futura."""
    t = pd.Timestamp(reference)
    if t.tzinfo is not None:
        raise ValueError("A referência deve usar o relógio sem timezone da fonte")
    if transactions.empty or transactions.InvoiceDate.isna().any():
        raise ValueError("Transações vazias ou com datas ausentes")
    if t < pd.Timestamp(bundle["selection"]["test_reference"]):
        raise ValueError("Modelo não disponível nessa referência histórica")
    # Último dia pode estar incompleto; default conservador, documentado.
    coverage = (transactions.InvoiceDate.max().normalize() if observed_through is None
                else pd.Timestamp(observed_through))
    if coverage.tzinfo is not None:
        raise ValueError("Limite de cobertura deve ser sem timezone")
    if t > coverage:
        raise ValueError("Referência posterior à cobertura; informe somente dados completos")
    history = transactions.loc[transactions.InvoiceDate < t]
    if history.empty:
        raise ValueError("Sem histórico anterior à referência")
    features = make_features(candidate_sales(history), t, history.InvoiceDate.min().normalize())
    with threadpool_limits(limits=2):
        regression = predict_nonnegative(bundle["model"], features)
    result = features[["CustomerID"]].copy()
    result["reference_date"] = t
    result["response_end_exclusive"] = t + pd.Timedelta(days=30)
    result["regressor_prediction_gbp"] = regression
    result["baseline_prediction_gbp"] = features.spend_90d.to_numpy() / 3
    # Decisão publicada após a avaliação: ML não superou a regra em RMSE.
    result["prediction_gbp"] = result.baseline_prediction_gbp
    result["recommended_method"] = "last_90d_div3"
    result["regressor_version"] = bundle["selection"]["selected"]["id"]
    return result
