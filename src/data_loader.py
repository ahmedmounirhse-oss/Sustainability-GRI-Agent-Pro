from pathlib import Path
from typing import Dict
import pandas as pd

from .config import DATA_DIR, INDICATORS, IndicatorSheet

# Mapping any possible month format → numeric month
MONTH_MAP = {
    "jan": 1, "january": 1, "01": 1, "1": 1,
    "feb": 2, "february": 2, "02": 2, "2": 2,
    "mar": 3, "march": 3, "03": 3, "3": 3,
    "apr": 4, "april": 4, "04": 4, "4": 4,
    "may": 5, "05": 5, "5": 5,
    "jun": 6, "june": 6, "06": 6, "6": 6,
    "jul": 7, "july": 7, "07": 7, "7": 7,
    "aug": 8, "august": 8, "08": 8, "8": 8,
    "sep": 9, "september": 9, "09": 9, "9": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,

    # Arabic formats
    "يناير": 1, "فبراير": 2, "مارس": 3, "ابريل": 4,
    "مايو": 5, "يونيو": 6, "يوليو": 7, "اغسطس": 8,
    "سبتمبر": 9, "اكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12
}


def normalize_month(value):
    """Converts any month format (text/number) into integer 1–12."""
    val = str(value).strip().lower()

    if val in MONTH_MAP:
        return MONTH_MAP[val]

    try:
        num = int(val)
        if 1 <= num <= 12:
            return num
    except:
        pass

    raise ValueError(f"Unrecognized month format: {value}")


# --------------------------------------------------------------
#       🔥 بدل discover_files → اعمل Auto-discovery لأي Excel
# --------------------------------------------------------------
def discover_files() -> Dict[str, Path]:
    """
    Returns ALL Excel files inside DATA_DIR automatically,
    regardless of naming format.
    """
    files: Dict[str, Path] = {}

    for path in DATA_DIR.glob("*.xlsx"):
        files[path.name] = path

    for path in DATA_DIR.glob("*.xls"):
        files[path.name] = path

    return dict(sorted(files.items()))


# --------------------------------------------------------------
#                   🔥 load_indicator
# --------------------------------------------------------------
def load_indicator(indicator_key: str) -> pd.DataFrame:
    if indicator_key not in INDICATORS:
        raise ValueError(f"Unknown indicator key: {indicator_key}")

    indicator: IndicatorSheet = INDICATORS[indicator_key]

    # auto-detect all files
    files = discover_files()

    if not files:
        raise ValueError("❌ No Excel files found inside data directory")

    frames = []

    for filename, path in files.items():
        df = pd.read_excel(path, sheet_name=indicator.sheet_name)

        expected_cols = {"Year", "Month", "Indicator", "Value", "Unit", "Remarks"}
        missing = expected_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns {missing} in {filename}")

        df["Year"] = df["Year"].astype(int)
        df["Month"] = df["Month"].apply(normalize_month)

        df = df.sort_values("Month")
        frames.append(df)

    data = pd.concat(frames, ignore_index=True)
    data.sort_values(["Year", "Month"], inplace=True)

    return data
