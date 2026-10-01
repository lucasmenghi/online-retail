"""Reconstrói somente o estimador congelado; não seleciona nem reabre o teste."""
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import joblib
from threadpoolctl import threadpool_limits
from src.model import build_model
from src.retail import FEATURES, RESPONSE, development_table, locate_data, read_transactions


if __name__ == "__main__":
    path = ROOT / "artifacts/retail_v1.joblib"
    if path.exists():
        raise SystemExit("O artefato já existe; preservado. Não é necessário reconstruí-lo.")
    report = ROOT / "reports/final"
    selection = json.loads((report / "selection.json").read_text(encoding="utf-8"))
    for package, expected in selection["packages"].items():
        if version(package) != expected:
            raise RuntimeError(f"Instale {package}=={expected} para reproduzir o ambiente")
    data = locate_data(ROOT)
    table = development_table(read_transactions(data))
    raw_hash = hashlib.sha256(data.read_bytes()).hexdigest()
    # CSVs equivalentes podem diferir em BOM, casas decimais e finais de linha.
    table_hash = hashlib.sha256(table.to_csv(index=False, float_format="%.17g", lineterminator="\n").encode("utf-8")).hexdigest()
    contract = json.loads((report / "rebuild_contract.json").read_text(encoding="utf-8"))
    if table_hash != contract["development_table_sha256"]:
        raise RuntimeError("Dados de treinamento diferentes da versão congelada; não reconstruir como v1.")
    model = build_model(selection["selected"])
    with threadpool_limits(limits=2):
        model.fit(table[FEATURES], table[RESPONSE])
    path.parent.mkdir(exist_ok=True)
    joblib.dump({"model": model, "selection": selection}, path)
    # Hash de serialização pode variar entre plataformas. O manifesto original é preservado.
    original = json.loads((report / "artifact_manifest.json").read_text(encoding="utf-8"))
    rebuilt_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if rebuilt_hash != original["sha256"] or raw_hash != selection["data_sha256"]:
        rebuilt_manifest = {"file": "artifacts/retail_v1.joblib", "sha256": rebuilt_hash,
                            "selection_sha256": hashlib.sha256((report / "selection.json").read_bytes()).hexdigest(),
                            "rebuilt": True, "original_artifact_sha256": original["sha256"],
                            "actual_data_sha256": raw_hash, "development_table_sha256": table_hash}
        (path.parent / "rebuilt_manifest.json").write_text(json.dumps(rebuilt_manifest, indent=2), encoding="utf-8")
        print("Reconstruído. Serialização difere da original: use artifacts/rebuilt_manifest.json para verificar a cópia.")
    else:
        print("Artefato reconstruído com hash idêntico ao original.")
