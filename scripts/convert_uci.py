"""Converte o XLSX oficial para o formato de leitura documentado."""
import argparse
from pathlib import Path
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsx", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/raw/Online Retail.csv"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("O arquivo de saída já existe; escolha outro caminho para preservá-lo.")
    frame = pd.read_excel(args.xlsx, dtype={"CustomerID": "string", "InvoiceNo": "string", "StockCode": "string"})
    frame["InvoiceDate"] = pd.to_datetime(frame.InvoiceDate).dt.strftime("%d/%m/%Y %H:%M")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, sep=";", decimal=",", index=False, encoding="utf-8-sig")
    print(f"Convertidas {len(frame):,} linhas para {args.output}")
