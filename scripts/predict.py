"""Gera previsões de 30 dias; CSV de saída contém ambos os métodos."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.inference import load_verified_bundle, predict_batch
from src.retail import locate_data, read_transactions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True, help="Data de referência YYYY-MM-DD, sem timezone")
    parser.add_argument("--data", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=ROOT / "reports/final/artifact_manifest.json")
    parser.add_argument("--observed-through", default=None, help="Limite exclusivo de cobertura completa declarado pelo operador")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Saída já existe; escolha outro caminho para preservar a execução anterior")
    bundle = load_verified_bundle(ROOT / "artifacts/retail_v1.joblib", args.manifest)
    predictions = predict_batch(read_transactions(args.data or locate_data(ROOT)), bundle, args.as_of,
                                observed_through=args.observed_through)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(args.output, index=False)
    print(f"Previsões: {len(predictions):,} clientes. Método recomendado: last_90d_div3.")
    print(f"Regressor congelado incluído em coluna separada. Saída: {args.output}")
