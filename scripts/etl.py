# scripts/etl.py
import os
import glob
import pandas as pd
from sklearn.preprocessing import StandardScaler

DATA_DIR = "data"
ETL_OUT = "output/etl"
os.makedirs(ETL_OUT, exist_ok=True)


# -------------------------------
#  ANOMALY DETECTION FUNCTION
# -------------------------------
def detect_anomalies(df, col):
    df[col] = pd.to_numeric(df[col], errors='coerce')
    values = df[col].fillna(df[col].mean()).values.reshape(-1, 1)

    scaler = StandardScaler()
    z_scores = scaler.fit_transform(values)
    df["z_score"] = z_scores

    flags = []
    for z in z_scores:
        if z > 2:
            flags.append("High Anomaly")
        elif z < -2:
            flags.append("Low Anomaly")
        elif abs(z) > 1.5:
            flags.append("Warning")
        else:
            flags.append("Normal")
    df["anomaly_flag"] = flags

    return df


# -------------------------------
#              ETL
# -------------------------------
def run_etl():
    records = []

    print("🔄 Starting ETL...")
    print(f"📂 Reading data from: {DATA_DIR}")

    for path in glob.glob(f"{DATA_DIR}/*"):
        try:
            print(f"➡️ Processing: {path}")

            if path.endswith(".csv"):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)

            df = df.dropna(how="all", axis=1)

            value_cols = [
                c for c in df.columns
                if c.lower() in [
                    "value", "energy_kwh", "co2", "co2_tons",
                    "water_m3", "waste_ton", "monthly_value"
                ]
            ]

            if value_cols:
                print(f"📊 Detecting anomalies for: {value_cols[0]}")
                df = detect_anomalies(df, value_cols[0])
            else:
                print("❗ No KPI column found (value, energy_kwh, co2, ...)")

            out_name = os.path.join(ETL_OUT, f"{os.path.basename(path)}.clean.csv")
            df.to_csv(out_name, index=False)
            records.append(out_name)

            print(f"✅ Saved cleaned file: {out_name}")

        except Exception as e:
            print(f"❌ Failed {path}: {e}")

    print("🎉 ETL Completed!")
    print(f"📁 Output written to: {ETL_OUT}")
    return records
if __name__ == "__main__":
    run_etl()
