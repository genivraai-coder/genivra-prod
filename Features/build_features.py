import pandas as pd
import os
from typing import List, Optional

def load_raw_data(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    return pd.read_csv(file_path)

def create_features(df: pd.DataFrame, biomarker_cols: Optional[List[str]] = None) -> pd.DataFrame:
    if biomarker_cols is None:
        biomarker_cols = [col for col in df.columns if "biomarker" in col.lower()]
    
    for col in biomarker_cols:
        df[f"{col}_z"] = (df[col] - df[col].mean()) / df[col].std()
    
    df["biomarker_count"] = df[biomarker_cols].notnull().sum(axis=1)
    df["has_all_biomarkers"] = df[biomarker_cols].notnull().all(axis=1).astype(int)
    
    return df

def save_features(df: pd.DataFrame, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)