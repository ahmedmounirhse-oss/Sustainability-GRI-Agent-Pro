from dataclasses import dataclass

@dataclass
class IndicatorMeta:
    kpi_name: str
    gri_code: str
    sheet_name: str

INDICATORS = {
    "energy": IndicatorMeta(
        kpi_name="Energy Consumption",
        gri_code="302",
        sheet_name="Energy_Consumption"
    ),
    "water": IndicatorMeta(
        kpi_name="Water Usage",
        gri_code="303",
        sheet_name="Water_Usage"
    ),
    "emissions": IndicatorMeta(
        kpi_name="Emissions",
        gri_code="305",
        sheet_name="Emissions"
    ),
    "waste": IndicatorMeta(
        kpi_name="Waste Generation",
        gri_code="306",
        sheet_name="Waste_Generation"
    ),
}
