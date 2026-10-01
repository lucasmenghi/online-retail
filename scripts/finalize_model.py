"""Refina, congela e avalia v1 em etapas explícitas e rastreáveis."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import joblib
import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.inspection import permutation_importance
from threadpoolctl import threadpool_limits

from src.evaluation import metrics
from src.model import build_model, candidate_specs, predict_nonnegative
from src.retail import (FEATURES, RESPONSE, TEST_REFERENCE, candidate_sales, development_table,
                        locate_data, make_snapshot, read_transactions, temporal_fold)

REPORTS = ROOT / "reports/final"
ARTIFACTS = ROOT / "artifacts"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def tune():
    REPORTS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(exist_ok=True)
    if (REPORTS / "selection.json").exists():
        raise RuntimeError("Seleção já congelada. Preserve a versão; não retune o mesmo teste.")
    table = development_table(read_transactions(locate_data(ROOT)))
    specs = candidate_specs()
    write_json(REPORTS / "search_space.json", specs)
    references = sorted(table.reference_date.unique())[3:]
    rows, summary, failures = [], [], []
    for i, spec in enumerate(specs, start=1):
        predictions = []
        candidate_rows = []
        try:
            for t in references:
                train, valid = temporal_fold(table, t)
                model = build_model(spec)
                with warnings.catch_warnings(), threadpool_limits(limits=2):
                    warnings.simplefilter("error", ConvergenceWarning)
                    warnings.simplefilter("error", RuntimeWarning)
                    model.fit(train[FEATURES], train[RESPONSE])
                    pred = predict_nonnegative(model, valid)
                candidate_rows.append({"candidate": spec["id"], "reference_date": pd.Timestamp(t),
                                       "train_n": len(train), **metrics(valid[RESPONSE], pred)})
                predictions.append(pd.DataFrame({"y": valid[RESPONSE].to_numpy(), "prediction": pred}))
            out = pd.concat(predictions, ignore_index=True)
            summary.append({"candidate": spec["id"], **metrics(out.y, out.prediction)})
            rows.extend(candidate_rows)
            print(f"[{i}/{len(specs)}] {spec['id']}: RMSE={summary[-1]['rmse_gbp']:.2f}", flush=True)
        except (ValueError, FloatingPointError, RuntimeWarning, ConvergenceWarning) as error:
            failures.append({"candidate": spec["id"], "error": str(error)})
            print(f"[{i}/{len(specs)}] {spec['id']}: excluído, {error}", flush=True)
    if not summary:
        raise RuntimeError("Todos os candidatos falharam")
    ranking = pd.DataFrame(summary).sort_values(["rmse_gbp", "candidate"])
    ranking.to_csv(REPORTS / "tuning_ranking.csv", index=False)
    pd.DataFrame(rows).to_csv(REPORTS / "tuning_folds.csv", index=False)
    write_json(REPORTS / "failed_candidates.json", failures)
    selected = next(s for s in specs if s["id"] == ranking.iloc[0].candidate)
    selection = {"version": "v1", "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                 "selected": selected, "selection_metric": "pooled_development_rmse_gbp",
                 "features": FEATURES, "response": RESPONSE, "lookback_days": 90, "horizon_days": 30,
                 "rules": {"deduplicate": False, "merchandise_only": False, "net_of_returns": False},
                 "data_sha256": digest(locate_data(ROOT)),
                 "code_sha256": {p: digest(ROOT / p) for p in ["src/retail.py", "src/model.py", "src/evaluation.py", "scripts/finalize_model.py"]},
                 "packages": {p: version(p) for p in ["numpy", "pandas", "scikit-learn", "joblib", "scipy"]},
                 "python": platform.python_version(), "train_rows": len(table),
                 "train_last_response_end": str(table.response_end.max()),
                 "test_reference": "2011-11-01", "test_response_end": "2011-12-01",
                 "test_evaluated_at_freeze": False, "production_approved": False}
    # Persistido antes de qualquer cálculo da resposta de novembro.
    write_json(REPORTS / "selection.json", selection)
    model = build_model(selected)
    with warnings.catch_warnings(), threadpool_limits(limits=2):
        warnings.simplefilter("error", ConvergenceWarning)
        model.fit(table[FEATURES], table[RESPONSE])
    artifact = ARTIFACTS / "retail_v1.joblib"
    joblib.dump({"model": model, "selection": selection}, artifact)
    write_json(REPORTS / "artifact_manifest.json", {"file": "artifacts/retail_v1.joblib", "sha256": digest(artifact),
               "selection_sha256": digest(REPORTS / "selection.json")})
    # Interpretação em outubro de desenvolvimento, sem consultar o teste.
    train, valid = temporal_fold(table, references[-1])
    interpretation_model = build_model(selected)
    with threadpool_limits(limits=2):
        interpretation_model.fit(train[FEATURES], train[RESPONSE])
        importance = permutation_importance(interpretation_model, valid[FEATURES], valid[RESPONSE],
                                            scoring="neg_mean_squared_error", n_repeats=5,
                                            random_state=42, n_jobs=1)
    pd.DataFrame({"feature": FEATURES, "increase_mse_gbp2": importance.importances_mean,
                  "std_gbp2": importance.importances_std}).sort_values("increase_mse_gbp2", ascending=False).to_csv(
                      REPORTS / "development_permutation_importance.csv", index=False)
    print("CONGELADO:", selected["id"], flush=True)


def evaluate():
    if (REPORTS / "holdout_metrics.csv").exists():
        raise RuntimeError("Novembro já foi avaliado; consulte o relatório existente.")
    selection = json.loads((REPORTS / "selection.json").read_text(encoding="utf-8"))
    artifact_info = json.loads((REPORTS / "artifact_manifest.json").read_text(encoding="utf-8"))
    if digest(REPORTS / "selection.json") != artifact_info["selection_sha256"]:
        raise ValueError("Seleção alterada após congelamento")
    if digest(ARTIFACTS / "retail_v1.joblib") != artifact_info["sha256"]:
        raise ValueError("Artefato alterado após congelamento")
    if digest(locate_data(ROOT)) != selection["data_sha256"]:
        raise ValueError("Dados alterados após congelamento")
    for relative, expected in selection["code_sha256"].items():
        if digest(ROOT / relative) != expected:
            raise ValueError(f"Código alterado após congelamento: {relative}")
    bundle = joblib.load(ARTIFACTS / "retail_v1.joblib")
    transactions = read_transactions(locate_data(ROOT))
    sales = candidate_sales(transactions)
    holdout = make_snapshot(sales, TEST_REFERENCE, transactions.InvoiceDate.min().normalize(),
                            transactions.InvoiceDate.max().normalize())
    with threadpool_limits(limits=2):
        pred = predict_nonnegative(bundle["model"], holdout)
    baseline = holdout.spend_90d.to_numpy() / 3
    y = holdout[RESPONSE].to_numpy()
    comparison = pd.DataFrame([{"model": selection["selected"]["id"], **metrics(y, pred)},
                               {"model": "last_90d_div3", **metrics(y, baseline)}])
    # A partir daqui o teste foi observado; não há nova seleção.
    comparison.to_csv(REPORTS / "holdout_metrics.csv", index=False)
    segments = []
    bands = pd.cut(holdout.spend_90d, [-np.inf, 500, 2000, np.inf], labels=["up_to_500", "500_to_2000", "above_2000"])
    for dimension, labels in [("repurchase", np.where(y == 0, "zero", "positive")), ("historical_spend", bands)]:
        for label in sorted(set(labels)):
            mask = np.asarray(labels == label)
            for name, values in [("regressor", pred), ("last_90d_div3", baseline)]:
                segments.append({"model": name, "dimension": dimension, "segment": str(label),
                                 **metrics(y[mask], values[mask])})
    pd.DataFrame(segments).to_csv(REPORTS / "holdout_segments.csv", index=False)
    calibration = pd.DataFrame({"observed": y, "prediction": pred})
    calibration["prediction_decile"] = pd.qcut(calibration.prediction.rank(method="first"), 10, labels=False) + 1
    calibration.groupby("prediction_decile").agg(n=("observed", "size"), observed_mean_gbp=("observed", "mean"),
                   prediction_mean_gbp=("prediction", "mean")).to_csv(REPORTS / "holdout_calibration.csv")
    rng = np.random.default_rng(42)
    deltas = []
    for _ in range(2000):
        index = rng.integers(0, len(y), size=len(y))
        deltas.append(float(np.sqrt(np.mean((pred[index] - y[index]) ** 2)) -
                            np.sqrt(np.mean((baseline[index] - y[index]) ** 2))))
    final = {"evaluated_at_utc": datetime.now(timezone.utc).isoformat(), "reference_date": "2011-11-01",
             "response_end_exclusive": "2011-12-01", "customers": len(y),
             "zero_response_pct": float(np.mean(y == 0) * 100),
             "regressor": selection["selected"]["id"],
             "rmse_improvement_pct": float(100 * (1 - comparison.iloc[0].rmse_gbp / comparison.iloc[1].rmse_gbp)),
             "paired_customer_bootstrap": {"resamples": 2000, "seed": 42,
                 "quantity": "regressor_rmse_minus_baseline_rmse_gbp", "ci95_percentile": np.quantile(deltas, [.025, .975]).tolist(),
                 "limitation": "Condicionado a novembro; não representa incerteza temporal, nem de seleção/treinamento."},
             "model_changed_after_test": False, "production_approved": False}
    write_json(REPORTS / "evaluation.json", final)
    # Previsões por cliente ficam apenas no diretório ignorado pelo Git.
    (ROOT / "reports/predictions").mkdir(exist_ok=True)
    holdout[["CustomerID", "reference_date", RESPONSE]].assign(prediction_gbp=pred, baseline_gbp=baseline).to_csv(
        ROOT / "reports/predictions/holdout_v1.csv", index=False)
    print(comparison.to_string(index=False), flush=True)
    print(json.dumps(final, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["tune", "evaluate"])
    args = parser.parse_args()
    tune() if args.stage == "tune" else evaluate()
