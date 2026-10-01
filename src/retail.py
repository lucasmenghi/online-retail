"""Leitura, regras experimentais e snapshots estritamente temporais."""
from pathlib import Path

import numpy as np
import pandas as pd

RESPONSE = "response_gbp_30d"
TEST_REFERENCE = pd.Timestamp("2011-11-01")
SPECIAL_CODES = {"POST", "DOT", "C2", "M", "BANK CHARGES", "D", "AMAZONFEE", "CRUK"}
FEATURES = ["recency_days", "observed_span_days"] + [
    f"{name}_{days}d" for days in (30, 60, 90)
    for name in ("spend", "orders", "products", "units", "ticket")
] + ["spend_recent_vs_previous_30d"]


def locate_data(root: Path) -> Path:
    for path in (root / "data/raw/Online Retail.csv", root / "Online Retail.csv"):
        if path.is_file():
            return path
    raise FileNotFoundError("Adicione Online Retail.csv em data/raw/ ou na raiz. Consulte data/README.md.")


def read_transactions(path: Path) -> pd.DataFrame:
    raw_bytes = path.read_bytes()
    try:
        raw_bytes.decode("utf-8-sig")
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        raw_bytes.decode("cp1252")
        encoding = "cp1252"
    strings = ["InvoiceNo", "StockCode", "Description", "CustomerID", "Country"]
    df = pd.read_csv(path, sep=";", decimal=",", encoding=encoding,
                     dtype={col: "string" for col in strings})
    expected = set(strings + ["InvoiceDate", "Quantity", "UnitPrice"])
    if set(df.columns) != expected:
        raise ValueError(f"Schema inesperado: {list(df.columns)}")
    for col in strings:
        df[col] = df[col].str.strip().replace("", pd.NA)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="%d/%m/%Y %H:%M", errors="raise")
    for col in ["Quantity", "UnitPrice"]:
        df[col] = pd.to_numeric(df[col], errors="raise")
    return df


def candidate_sales(df: pd.DataFrame, *, deduplicate: bool = False,
                    merchandise_only: bool = False) -> pd.DataFrame:
    """Preserva duplicatas/códigos por padrão; variantes são análises de sensibilidade."""
    required = ["CustomerID", "InvoiceNo", "StockCode", "InvoiceDate", "Quantity", "UnitPrice"]
    valid = (df[required].notna().all(axis=1)
             & ~df.InvoiceNo.str.upper().str.startswith("C", na=False)
             & df.Quantity.gt(0) & df.UnitPrice.gt(0)
             & np.isfinite(df.Quantity) & np.isfinite(df.UnitPrice))
    sales = df.loc[valid].copy()
    if deduplicate:
        sales = sales.drop_duplicates()
    if merchandise_only:
        sales = sales.loc[~sales.StockCode.str.upper().isin(SPECIAL_CODES)].copy()
    sales["value_gbp"] = sales.Quantity * sales.UnitPrice
    if not np.isfinite(sales.value_gbp).all():
        raise ValueError("Valor monetário não finito")
    return sales


def make_snapshot(sales: pd.DataFrame, reference: pd.Timestamp,
                  observed_start: pd.Timestamp, observed_end: pd.Timestamp) -> pd.DataFrame:
    """Features em [t-90,t); resposta em [t,t+30); datas sem timezone da fonte."""
    t = pd.Timestamp(reference)
    if t - pd.Timedelta(days=90) < observed_start:
        raise ValueError("Histórico de 90 dias incompleto")
    if t + pd.Timedelta(days=30) > observed_end:
        raise ValueError("Horizonte da variável resposta incompleto")
    past = sales.loc[sales.InvoiceDate.ge(t - pd.Timedelta(days=90)) & sales.InvoiceDate.lt(t)]
    groups = past.groupby("CustomerID")
    result = pd.DataFrame(index=pd.Index(sorted(past.CustomerID.unique()), name="CustomerID"))
    result["recency_days"] = (t - groups.InvoiceDate.max()).dt.total_seconds() / 86400
    result["observed_span_days"] = (t - groups.InvoiceDate.min()).dt.total_seconds() / 86400
    for days in (30, 60, 90):
        window = past.loc[past.InvoiceDate.ge(t - pd.Timedelta(days=days))]
        g = window.groupby("CustomerID")
        result[f"spend_{days}d"] = g.value_gbp.sum()
        result[f"orders_{days}d"] = g.InvoiceNo.nunique()
        result[f"products_{days}d"] = g.StockCode.nunique()
        result[f"units_{days}d"] = g.Quantity.sum()
        result[f"ticket_{days}d"] = result[f"spend_{days}d"] / result[f"orders_{days}d"]
    result = result.fillna(0)
    # Diferença assinada, sem divisão instável por valores próximos de zero.
    result["spend_recent_vs_previous_30d"] = 2 * result.spend_30d - result.spend_60d
    future = sales.loc[sales.InvoiceDate.ge(t) & sales.InvoiceDate.lt(t + pd.Timedelta(days=30))]
    result[RESPONSE] = future.groupby("CustomerID").value_gbp.sum().reindex(result.index, fill_value=0)
    result["reference_date"] = t
    result["response_end"] = t + pd.Timedelta(days=30)
    expected = future.loc[future.CustomerID.isin(result.index), "value_gbp"].sum()
    if not np.isclose(result[RESPONSE].sum(), expected):
        raise AssertionError("Falha de reconciliação da variável resposta")
    if not np.isfinite(result[FEATURES + [RESPONSE]].to_numpy(dtype=float)).all():
        raise ValueError("Snapshot contém valores não finitos")
    return result.reset_index()


def development_table(df: pd.DataFrame, **sales_options) -> pd.DataFrame:
    # Não calcula a resposta de novembro. A reserva permanece fora do experimento.
    dev = df.loc[df.InvoiceDate < TEST_REFERENCE]
    sales = candidate_sales(dev, **sales_options)
    start = df.InvoiceDate.min().normalize()
    references = pd.date_range(start + pd.Timedelta(days=90), TEST_REFERENCE, freq="MS")
    frames = [make_snapshot(sales, t, start, TEST_REFERENCE) for t in references
              if t + pd.Timedelta(days=30) <= TEST_REFERENCE]
    if not frames:
        raise ValueError("Sem referências completas de desenvolvimento")
    table = pd.concat(frames, ignore_index=True)
    if table.duplicated(["CustomerID", "reference_date"]).any():
        raise AssertionError("Cliente/referência duplicado")
    return table


def temporal_fold(table: pd.DataFrame, reference: pd.Timestamp):
    t = pd.Timestamp(reference)
    train = table.loc[(table.reference_date < t) & (table.response_end <= t)].copy()
    validation = table.loc[table.reference_date.eq(t)].copy()
    if train.empty or validation.empty:
        raise ValueError("Fold sem treino ou validação")
    if train.response_end.max() > validation.reference_date.min():
        raise AssertionError("Resposta de treino invade a validação")
    return train, validation
