from typing import Optional
import pandas as pd


def build_indicator_narrative(
    indicator_key: str,
    df: pd.DataFrame,
    year: int,
    unit_label: str = "",
) -> str:
    """
    Builds a short professional GRI-style narrative for an indicator
    based on the selected year.

    Used in:
    - PDF reports
    - KPI fallback answer
    """

    df_year = df[df["Year"] == year]
    if df_year.empty:
        return f"No available data for {year}."

    total = df_year["Value"].sum()

    # Monthly pattern analysis
    peak_month = df_year.loc[df_year["Value"].idxmax()]["Month"]
    peak_value = df_year["Value"].max()

    low_month = df_year.loc[df_year["Value"].idxmin()]["Month"]
    low_value = df_year["Value"].min()

    # Basic narrative depending on indicator type
    names = {
        "energy": "Energy consumption",
        "water": "Water withdrawal and consumption",
        "emissions": "GHG emissions performance",
        "waste": "Waste generation and disposal",
    }

    name = names.get(indicator_key, "KPI performance")

    text = (
        f"In {year}, the organization reported a total {name.lower()} "
        f"of <b>{total:,.2f} {unit_label}</b>. Monthly data shows that "
        f"the highest recorded value occurred in month <b>{peak_month}</b> "
        f"with <b>{peak_value:,.2f} {unit_label}</b>, while the lowest "
        f"occurred in month <b>{low_month}</b> with <b>{low_value:,.2f} {unit_label}</b>. "
        f"The data was monitored throughout the year to ensure accuracy, improve "
        f"operational control, and support decision-making toward efficiency and "
        f"resource optimization."
    )

    return text
