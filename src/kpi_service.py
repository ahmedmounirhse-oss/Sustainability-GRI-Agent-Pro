import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def compute_yearly_totals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes total KPI values grouped by year and calculates YoY change.
    """
    yearly = df.groupby("Year")["Value"].sum().reset_index()
    yearly.rename(columns={"Value": "total_value"}, inplace=True)

    yearly["change_abs"] = yearly["total_value"].diff()
    yearly["change_pct"] = yearly["total_value"].pct_change() * 100

    return yearly


def forecast_next_year(yearly_df: pd.DataFrame):
    """
    Performs simple linear regression to predict KPI for the next year.
    Returns: (next_year, predicted_value)
    """
    if len(yearly_df) < 2:
        # Not enough data to forecast
        last_year = int(yearly_df["Year"].max())
        last_val = float(yearly_df["total_value"].iloc[-1])
        return last_year + 1, last_val

    X = yearly_df["Year"].values.reshape(-1, 1)
    y = yearly_df["total_value"].values.reshape(-1, 1)

    model = LinearRegression()
    model.fit(X, y)

    next_year = int(yearly_df["Year"].max()) + 1
    prediction = float(model.predict(np.array([[next_year]])).ravel()[0])

    return next_year, prediction
