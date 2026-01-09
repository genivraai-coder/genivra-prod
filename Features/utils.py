import pandas as pd
import os
from typing import List, Optional

def validate_columns(df: pd.DataFrame, required_cols: List[str]) -> None:
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

def drop_missing_rows(df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
    return df.dropna(subset=subset)

def filter_by_threshold(df: pd.DataFrame, col: str, min_value: Optional[float] = None, max_value: Optional[float] = None) -> pd.DataFrame:
    if min_value is not None:
        df = df[df[col] >= min_value]
    if max_value is not None:
        df = df[df[col] <= max_value]
    return df

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(path)

def save_csv(df: pd.DataFrame, path: str) -> None:
    ensure_dir(os.path.dirname(path))
    df.to_csv(path, index=False)