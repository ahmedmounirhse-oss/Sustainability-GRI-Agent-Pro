import os
import glob
import pandas as pd
from .config import INDICATORS


# -----------------------------------------------------------
# 🔥 MONTH NORMALIZATION (English + Arabic + Numbers)
# -----------------------------------------------------------
MONTH_MAP = {
    "jan": 1, "january": 1, "يناير": 1,
    "feb": 2, "february": 2, "فبراير": 2,
    "mar": 3, "march": 3, "مارس": 3,
    "apr": 4, "april": 4, "ابريل": 4,
    "may": 5, "مايو": 5,
    "jun": 6, "june": 6, "يونيو": 6,
    "jul": 7, "july": 7, "يوليو": 7,
    "aug": 8, "august": 8, "اغسطس": 8,
    "sep": 9, "september": 9, "سبتمبر": 9,
    "oct": 10, "october": 10, "اكتوبر": 10,
    "nov": 11, "november": 11, "نوفمبر": 11,
    "dec": 12, "december": 12, "ديسمبر": 12,
}

def normalize_month(value):
    """Converts any Month format into integer 1–12."""
    value = str(value).strip().lower()

    if value in MONTH_MAP:
        return MONTH_MAP[value]

    # Try convert to int directly
    try:
        num = int(value)
        if 1 <= num <= 12:
            return num
    except:
        pass

    raise ValueError(f"❌ Unrecognized month format: '{value}'")


# -----------------------------------------------------------
# 🔥 AUTO DISCOVER ALL EXCEL FILES IN /data
# -----------------------------------------------------------
def discover_files(data_dir: str = "data"):
    files = []
    for ext in ("*.xlsx", "*.xls"):
        files.extend(glob.glob(os.path.join(data_dir, ext)))

    if not files:
        raise FileNotFoundError("❌ No Excel files found inside /data folder.")

    return files


# -----------------------------------------------------------
# 🔥 LOAD INDICATOR SHEET FROM ALL FILES (2015–2022)
# -----------------------------------------------------------
def load_indicator(indicator_key: str) -> pd.DataFrame:
    if indicator_key not in INDICATORS:
        raise ValueError(f"❌ Unknown indicator key: {indicator_key}")

    sheet_name = INDICATORS[indicator_key].sheet_name
    files = discover_files()

    frames = []

    for file_path in files:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            raise ValueError(f"❌ Cannot read sheet '{sheet_name}' in file '{file_path}': {e}")

        # Required columns
        required = {"Year", "Value"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"❌ Missing required columns {missing} in sheet '{sheet_name}' in file {file_path}")

        # Optional columns
        if "Unit" not in df.columns:
            df["Unit"] = "unit"

        if "Month" not in df.columns:
            df["Month"] = 1  # assume yearly aggregated
        else:
            df["Month"] = df["Month"].apply(normalize_month)

        df["Year"] = df["Year"].astype(int)

        frames.append(df)

    # Merge all files into one DF
    data = pd.concat(frames, ignore_index=True)
    data.sort_values(["Year", "Month"], inplace=True)

    return data
