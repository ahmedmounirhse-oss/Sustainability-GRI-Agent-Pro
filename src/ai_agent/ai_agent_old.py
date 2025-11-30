"""
SustainabilityAgentPro – Unified LLM + Reporting + KPI + Anomaly Engine
File: src/ai_agent/agent.py

Combines:
- Old LLM-powered SustainabilityAgent (indicator detection + KPI + forecasting + narratives)
- New Analytical Agent (anomalies, yearly totals, CSV export, PDF summary, auto loading)

This is now the MAIN agent for the project.
"""

from __future__ import annotations
import re
import os
import glob
from typing import Literal, Dict, Any, List, Optional
import pandas as pd
import numpy as np

from .config import INDICATORS
from .data_loader import load_indicator
from .kpi_service import compute_yearly_totals, forecast_next_year
from .reporting import build_indicator_narrative
from .llm_engine import generate_sustainability_answer

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

IndicatorKey = Literal["energy", "water", "emissions", "waste"]

# ----------------------- UTILITIES -----------------------
def detect_anomalies(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    s = series.dropna()
    mu, sigma = s.mean(), s.std(ddof=0)
    if sigma == 0 or np.isnan(sigma):
        return pd.Series(False, index=series.index)
    z = (series - mu) / sigma
    return z.abs() > threshold


def anomaly_stats(series: pd.Series) -> Dict[str, Any]:
    return {
        "mean": float(series.mean()),
        "std": float(series.std(ddof=0)),
        "min": float(series.min()),
        "max": float(series.max()),
        "count": int(series.count()),
    }


# ----------------------- REPORT GENERATOR -----------------------
class ReportGenerator:
    def __init__(self, out_dir: str = "output"):
        os.makedirs(out_dir, exist_ok=True)
        self.out_dir = out_dir

    def write_csv(self, key: str, df: pd.DataFrame) -> str:
        path = os.path.join(self.out_dir, f"{key}_analysis.csv")
        df.to_csv(path, index=False)
        return path

    def write_pdf(self, key: str, yearly: pd.DataFrame, anomalies: pd.DataFrame, unit: str) -> str:
        pdf_path = os.path.join(self.out_dir, f"{key}_summary.pdf")

        # Plot first
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(yearly["Year"], yearly["total_value"], marker="o")
        ax.set_title(f"{key} – KPI Trend")
        ax.set_xlabel("Year")
        ax.set_ylabel(unit)
        fig.tight_layout()

        img_path = os.path.join(self.out_dir, f"{key}_plot.png")
        fig.savefig(img_path)
        plt.close(fig)

        # Build PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, 750, f"Indicator Report: {key}")
        c.setFont("Helvetica", 10)
        c.drawImage(img_path, 40, 470, width=520, height=240)

        y = 450
        c.drawString(40, y, "Anomalies:")
        y -= 14
        for _, r in anomalies.iterrows():
            c.drawString(40, y, f"{int(r['Year'])} – {r['total_value']}")
            y -= 12
        c.save()

        return pdf_path


# ----------------------- COMBINED AGENT -----------------------
class SustainabilityAgentPro:
    """
    Combines:
    - Indicator detection
    - KPI analysis
    - Year detection
    - Forecasting
    - Anomaly detection
    - PDF/CSV reports
    - LLM answer generation
    """

    def __init__(self, data_dir: str = "data", out_dir: str = "output"):
        self._cache: Dict[str, pd.DataFrame] = {}
        self.data_dir = data_dir
        self.reporter = ReportGenerator(out_dir)

    # ------------------ Data Loader ------------------
    def _get_data(self, key: str) -> pd.DataFrame:
        if key not in self._cache:
            # auto-search files
            candidates = glob.glob(os.path.join(self.data_dir, f"**/*{key}*"), recursive=True)
            if not candidates:
                raise FileNotFoundError(f"No data file found for indicator: {key}")
            df = load_indicator(key)
            self._cache[key] = df
        return self._cache[key]

    # ------------------ Indicator Detection ------------------
    @staticmethod
    def _detect_indicator(q: str) -> Optional[str]:
        q = q.lower()
        if any(x in q for x in ["energy", "electricity", "302"]):
            return "energy"
        if any(x in q for x in ["water", "303"]):
            return "water"
        if any(x in q for x in ["emission", "co2", "ghg", "305"]):
            return "emissions"
        if any(x in q for x in ["waste", "306"]):
            return "waste"
        return None

    # ------------------ Year Detection ------------------
    @staticmethod
    def _detect_years(q: str, df: pd.DataFrame) -> List[int]:
        found = [int(y) for y in re.findall(r"(20[0-9]{2})", q)]
        if found:
            return found
        return [int(df["Year"].max())]

    # ------------------ MAIN ------------------
    def answer(self, query: str) -> str:
        key = self._detect_indicator(query)

        # No indicator → general LLM
        if key is None:
            return generate_sustainability_answer(query, {"general_question": True})

        meta = INDICATORS[key]
        df = self._get_data(key)
        unit = df["Unit"].iloc[0]

        # KPI
        yearly = compute_yearly_totals(df)

        # years
        years_req = self._detect_years(query, df)
        avail_years = yearly["Year"].tolist()
        valid_years = [y for y in years_req if y in avail_years]
        if not valid_years:
            return f"Requested years not found. Available: {avail_years}"

        # Forecast
        try:
            next_year, pred = forecast_next_year(yearly)
        except Exception:
            next_year, pred = None, None

        # Anomalies
        yearly["anomaly"] = detect_anomalies(yearly["total_value"])
        anomalies = yearly[yearly["anomaly"]]
        anomaly_info = anomaly_stats(yearly["total_value"])

        # Narratives
        narratives = {
            y: build_indicator_narrative(key, df, y, unit_label=unit)
            for y in valid_years
        }

        # Reports
        csv_path = self.reporter.write_csv(key, yearly)
        pdf_path = self.reporter.write_pdf(key, yearly, anomalies, unit)

        # LLM Context
        context = {
            "indicator_key": key,
            "indicator_name": meta.kpi_name,
            "gri_code": meta.gri_code,
            "unit": unit,
            "years": valid_years,
            "kpis": yearly.to_dict(orient="records"),
            "narratives": narratives,
            "anomaly_summary": anomaly_info,
            "anomalies": anomalies.to_dict(orient="records"),
            "forecast": {
                "next_year": next_year,
                "predicted_value": float(pred) if pred else None,
            },
            "reports": {"csv": csv_path, "pdf": pdf_path},
        }

        # Generate final LLM answer
        return generate_sustainability_answer(query, context)


# ------------------ CLI ------------------
if __name__ == "__main__":
    agent = SustainabilityAgentPro()
    q = input("Ask a sustainability question: ")
    print(agent.answer(q))
"""
SustainabilityAgentPro – Unified LLM + Reporting + KPI + Anomaly Engine
File: src/ai_agent/agent.py

Combines:
- Old LLM-powered SustainabilityAgent (indicator detection + KPI + forecasting + narratives)
- New Analytical Agent (anomalies, yearly totals, CSV export, PDF summary, auto loading)

This is now the MAIN agent for the project.
"""

from __future__ import annotations
import re
import os
import glob
from typing import Literal, Dict, Any, List, Optional
import pandas as pd
import numpy as np

from .config import INDICATORS
from .data_loader import load_indicator
from .kpi_service import compute_yearly_totals, forecast_next_year
from .reporting import build_indicator_narrative
from .llm_engine import generate_sustainability_answer

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

IndicatorKey = Literal["energy", "water", "emissions", "waste"]

# ----------------------- UTILITIES -----------------------
def detect_anomalies(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    s = series.dropna()
    mu, sigma = s.mean(), s.std(ddof=0)
    if sigma == 0 or np.isnan(sigma):
        return pd.Series(False, index=series.index)
    z = (series - mu) / sigma
    return z.abs() > threshold


def anomaly_stats(series: pd.Series) -> Dict[str, Any]:
    return {
        "mean": float(series.mean()),
        "std": float(series.std(ddof=0)),
        "min": float(series.min()),
        "max": float(series.max()),
        "count": int(series.count()),
    }


# ----------------------- REPORT GENERATOR -----------------------
class ReportGenerator:
    def __init__(self, out_dir: str = "output"):
        os.makedirs(out_dir, exist_ok=True)
        self.out_dir = out_dir

    def write_csv(self, key: str, df: pd.DataFrame) -> str:
        path = os.path.join(self.out_dir, f"{key}_analysis.csv")
        df.to_csv(path, index=False)
        return path

    def write_pdf(self, key: str, yearly: pd.DataFrame, anomalies: pd.DataFrame, unit: str) -> str:
        pdf_path = os.path.join(self.out_dir, f"{key}_summary.pdf")

        # Plot first
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(yearly["Year"], yearly["total_value"], marker="o")
        ax.set_title(f"{key} – KPI Trend")
        ax.set_xlabel("Year")
        ax.set_ylabel(unit)
        fig.tight_layout()

        img_path = os.path.join(self.out_dir, f"{key}_plot.png")
        fig.savefig(img_path)
        plt.close(fig)

        # Build PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, 750, f"Indicator Report: {key}")
        c.setFont("Helvetica", 10)
        c.drawImage(img_path, 40, 470, width=520, height=240)

        y = 450
        c.drawString(40, y, "Anomalies:")
        y -= 14
        for _, r in anomalies.iterrows():
            c.drawString(40, y, f"{int(r['Year'])} – {r['total_value']}")
            y -= 12
        c.save()

        return pdf_path


# ----------------------- COMBINED AGENT -----------------------
class SustainabilityAgentPro:
    """
    Combines:
    - Indicator detection
    - KPI analysis
    - Year detection
    - Forecasting
    - Anomaly detection
    - PDF/CSV reports
    - LLM answer generation
    """

    def __init__(self, data_dir: str = "data", out_dir: str = "output"):
        self._cache: Dict[str, pd.DataFrame] = {}
        self.data_dir = data_dir
        self.reporter = ReportGenerator(out_dir)

    # ------------------ Data Loader ------------------
    def _get_data(self, key: str) -> pd.DataFrame:
        if key not in self._cache:
            # auto-search files
            candidates = glob.glob(os.path.join(self.data_dir, f"**/*{key}*"), recursive=True)
            if not candidates:
                raise FileNotFoundError(f"No data file found for indicator: {key}")
            df = load_indicator(key)
            self._cache[key] = df
        return self._cache[key]

    # ------------------ Indicator Detection ------------------
    @staticmethod
    def _detect_indicator(q: str) -> Optional[str]:
        q = q.lower()
        if any(x in q for x in ["energy", "electricity", "302"]):
            return "energy"
        if any(x in q for x in ["water", "303"]):
            return "water"
        if any(x in q for x in ["emission", "co2", "ghg", "305"]):
            return "emissions"
        if any(x in q for x in ["waste", "306"]):
            return "waste"
        return None

    # ------------------ Year Detection ------------------
    @staticmethod
    def _detect_years(q: str, df: pd.DataFrame) -> List[int]:
        found = [int(y) for y in re.findall(r"(20[0-9]{2})", q)]
        if found:
            return found
        return [int(df["Year"].max())]

    # ------------------ MAIN ------------------
    def answer(self, query: str) -> str:
        key = self._detect_indicator(query)

        # No indicator → general LLM
        if key is None:
            return generate_sustainability_answer(query, {"general_question": True})

        meta = INDICATORS[key]
        df = self._get_data(key)
        unit = df["Unit"].iloc[0]

        # KPI
        yearly = compute_yearly_totals(df)

        # years
        years_req = self._detect_years(query, df)
        avail_years = yearly["Year"].tolist()
        valid_years = [y for y in years_req if y in avail_years]
        if not valid_years:
            return f"Requested years not found. Available: {avail_years}"

        # Forecast
        try:
            next_year, pred = forecast_next_year(yearly)
        except Exception:
            next_year, pred = None, None

        # Anomalies
        yearly["anomaly"] = detect_anomalies(yearly["total_value"])
        anomalies = yearly[yearly["anomaly"]]
        anomaly_info = anomaly_stats(yearly["total_value"])

        # Narratives
        narratives = {
            y: build_indicator_narrative(key, df, y, unit_label=unit)
            for y in valid_years
        }

        # Reports
        csv_path = self.reporter.write_csv(key, yearly)
        pdf_path = self.reporter.write_pdf(key, yearly, anomalies, unit)

        # LLM Context
        context = {
            "indicator_key": key,
            "indicator_name": meta.kpi_name,
            "gri_code": meta.gri_code,
            "unit": unit,
            "years": valid_years,
            "kpis": yearly.to_dict(orient="records"),
            "narratives": narratives,
            "anomaly_summary": anomaly_info,
            "anomalies": anomalies.to_dict(orient="records"),
            "forecast": {
                "next_year": next_year,
                "predicted_value": float(pred) if pred else None,
            },
            "reports": {"csv": csv_path, "pdf": pdf_path},
        }

        # Generate final LLM answer
        return generate_sustainability_answer(query, context)


# ------------------ CLI ------------------
if __name__ == "__main__":
    agent = SustainabilityAgentPro()
    q = input("Ask a sustainability question: ")
    print(agent.answer(q))
