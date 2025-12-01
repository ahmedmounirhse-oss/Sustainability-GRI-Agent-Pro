import re
from typing import Literal, Dict, Any, List

import pandas as pd

from .config import INDICATORS
from .data_loader import load_indicator
from .kpi_service import compute_yearly_totals, forecast_next_year
from .reporting import build_indicator_narrative
from .llm_engine import generate_sustainability_answer

IndicatorKey = Literal["energy", "water", "emissions", "waste"]


class SustainabilityAgent:
    """
    Advanced Sustainability AI Agent:
    - Handles KPI analysis (energy, water, emissions, waste)
    - Provides GRI-aligned narratives
    - Answers general questions about GRI standards
    - Answers personal/meta questions (“Who are you?”)
    - Supports forecasting for next year
    """

    def __init__(self) -> None:
        pass  # 🔥 no cache anymore

    # --------------------------------------------------------------
    #                         DATA LOADING
    # --------------------------------------------------------------
    def _get_data(self, indicator_key: IndicatorKey) -> pd.DataFrame:
        # 🔥 always reload from /data/ — no caching
        return load_indicator(indicator_key)

    # --------------------------------------------------------------
    #                  SMART INDICATOR DETECTION
    # --------------------------------------------------------------
    @staticmethod
    def _detect_indicator(query: str):
        q = query.lower()

        if any(x in q for x in ["energy", "electricity", "power", "302"]):
            return "energy"
        if any(x in q for x in ["water", "303"]):
            return "water"
        if any(x in q for x in ["emission", "co2", "carbon", "ghg", "305"]):
            return "emissions"
        if any(x in q for x in ["waste", "306"]):
            return "waste"

        return None

    # --------------------------------------------------------------
    #                         YEAR DETECTION
    # --------------------------------------------------------------
    @staticmethod
    def _detect_years(query: str, df: pd.DataFrame) -> List[int]:
        years_found = [int(y) for y in re.findall(r"\b(20[0-9]{2})\b", query)]
        if years_found:
            return years_found

        return [int(df["Year"].max())]

    # --------------------------------------------------------------
    #                         MAIN LOGIC
    # --------------------------------------------------------------
    def answer(self, query: str) -> str:

        indicator_key = self._detect_indicator(query)

        # GENERAL QUESTION (NO INDICATOR)
        if indicator_key is None:
            return generate_sustainability_answer(
                query,
                {"general_question": True}
            )

        meta = INDICATORS[indicator_key]
        df = self._get_data(indicator_key)
        yearly = compute_yearly_totals(df)

        # YEARS
        years_requested = self._detect_years(query, df)
        available_years = yearly["Year"].tolist()

        years_valid = [y for y in years_requested if y in available_years]
        if not years_valid:
            raise ValueError(f"Requested years not found. Available: {available_years}")

        # FORECASTING
        try:
            next_year, prediction = forecast_next_year(yearly)
        except Exception:
            next_year, prediction = None, None

        # KPI PACKAGING
        unit = df["Unit"].iloc[0]
        kpi_records = []
        narratives = {}

        for year in years_valid:
            row = yearly[yearly["Year"] == year].iloc[0]

            kpi_records.append({
                "year": int(year),
                "total_value": float(row["total_value"]),
                "change_abs": None if pd.isna(row["change_abs"]) else float(row["change_abs"]),
                "change_pct": None if pd.isna(row["change_pct"]) else float(row["change_pct"]),
                "unit": unit,
            })

            narratives[year] = build_indicator_narrative(
                indicator_key, df, year, unit_label=unit
            )

        # LLM CONTEXT
        kpi_context = {
            "indicator_key": indicator_key,
            "indicator_name": meta.kpi_name,
            "gri_code": meta.gri_code,
            "unit": unit,
            "years": years_valid,
            "kpis": kpi_records,
            "base_narratives": narratives,
            "forecast": {
                "next_year": next_year,
                "predicted_value": float(prediction) if prediction else None
            }
        }

        # LLM ANSWER
        try:
            return generate_sustainability_answer(query, kpi_context)

        except Exception as exc:
            fb = []

            fb.append(f"Indicator: {meta.kpi_name} ({meta.gri_code})")
            fb.append(f"Unit: {unit}\n")

            for rec in kpi_records:
                abs_change = "n/a" if rec["change_abs"] is None else f"{rec['change_abs']:,.2f} {unit}"
                pct_change = "n/a" if rec["change_pct"] is None else f"{rec['change_pct']:.2f}%"

                fb.append(
                    f"Year {rec['year']}: {rec['total_value']:,.2f} {unit} "
                    f"(change: {abs_change}, {pct_change})"
                )
                fb.append(narratives[rec["year"]])
                fb.append("")

            if next_year and prediction:
                fb.append(f"Forecast for {next_year}: {prediction:,.2f} {unit}")

            fb.append(f"\n[LLM Error: {exc}]")

            return "\n".join(fb)
