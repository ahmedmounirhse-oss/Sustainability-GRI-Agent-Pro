from pathlib import Path
from dataclasses import dataclass
from typing import Dict

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Pattern for the Excel files, e.g. "Sustainability_data 2022.xlsx"
EXCEL_PATTERN = "Sustainability_data *.xlsx"


@dataclass(frozen=True)
class IndicatorSheet:
    key: str
    sheet_name: str
    gri_code: str
    kpi_name: str


# Define the four main indicators
INDICATORS: Dict[str, IndicatorSheet] = {
    "energy": IndicatorSheet(
        key="energy",
        sheet_name="Energy_Consumption",
        gri_code="GRI 302",
        kpi_name="Energy Consumption",
    ),
    "water": IndicatorSheet(
        key="water",
        sheet_name="Water_Usage",
        gri_code="GRI 303",
        kpi_name="Water Usage",
    ),
    "emissions": IndicatorSheet(
        key="emissions",
        sheet_name="Emissions",
        gri_code="GRI 305",
        kpi_name="GHG Emissions",
    ),
    "waste": IndicatorSheet(
        key="waste",
        sheet_name="Waste_Generation",
        gri_code="GRI 306",
        kpi_name="Waste Generation",
    ),
}
