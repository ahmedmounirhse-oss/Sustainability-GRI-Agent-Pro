# src/data_loader.py
from pathlib import Path
import pandas as pd
from .config import DATA_DIR, INDICATORS, IndicatorSheet

def discover_files():
    """Return all Excel files from data folder."""
    files = {}
    for ext in ("*.xlsx", "*.xls"):
        for path in Path(DATA_DIR).glob(ext):
            files[path.name] = path
    return dict(sorted(files.items()))

def normalize_month(value):
    try:
        return int(value)
    except:
        return value

def load_indicator(indicator_key: str) -> pd.DataFrame:
    """ALWAYS reload fresh data from data/ folder"""
    if indicator_key not in INDICATORS:
        raise ValueError(f"Unknown indicator: {indicator_key}")

    indicator: IndicatorSheet = INDICATORS[indicator_key]
    files = discover_files()

    if not files:
        raise ValueError("No Excel files found in /data folder")

    frames = []

    for name, path in files.items():
        df = pd.read_excel(path, sheet_name=indicator.sheet_name)

        expected = {"Year", "Month", "Indicator", "Value", "Unit"}
        missing = expected - set(df.columns)
        if missing:
            raise ValueError(f"File {name} missing columns: {missing}")

        df["Year"] = df["Year"].astype(int)
        df["Month"] = df["Month"].apply(normalize_month)
        df = df.sort_values("Month")

        frames.append(df)

    data = pd.concat(frames, ignore_index=True)
    data.sort_values(["Year", "Month"], inplace=True)
    return data
