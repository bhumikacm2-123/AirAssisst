
import pandas as pd
import matplotlib.pyplot as plt
import os

print("AirAssist historical EDA started!")

# Load cleaned historical data
file_path = "data/processed/historical_air_quality_cleaned.csv"
df = pd.read_csv(file_path)

df["Sampling Date"] = pd.to_datetime(df["Sampling Date"])

# Create output folders
os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/visualizations", exist_ok=True)

# 1. City-wise average pollution
pollutants = ["SO2", "NO2", "RSPM/PM10", "PM 2.5"]

city_summary = df.groupby(
    "City/Town/Village/Area"
)[pollutants].mean().round(2)

print("\nCITY-WISE AVERAGE POLLUTION:")
print(city_summary)

city_summary.to_csv(
    "data/processed/historical_city_summary.csv"
)

# 2. Monthly PM10 analysis
df["Month"] = df["Sampling Date"].dt.month

monthly_pm10 = df.groupby("Month")["RSPM/PM10"].mean()

print("\nMONTHLY AVERAGE PM10:")
print(monthly_pm10.round(2))

monthly_pm10.to_csv(
    "data/processed/monthly_pm10_summary.csv"
)

# 3. City-wise PM10 graph
city_pm10 = city_summary["RSPM/PM10"].sort_values(
    ascending=False
)

plt.figure(figsize=(10, 6))
city_pm10.plot(kind="bar")
plt.title("Average PM10 Pollution by City - Tamil Nadu 2015")
plt.xlabel("City")
plt.ylabel("Average PM10")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(
    "data/visualizations/historical_city_pm10.png"
)
plt.close()

# 4. Monthly PM10 graph
plt.figure(figsize=(10, 6))
monthly_pm10.plot(kind="line", marker="o")
plt.title("Monthly PM10 Pollution Trend - Tamil Nadu 2015")
plt.xlabel("Month")
plt.ylabel("Average PM10")
plt.xticks(range(1, 13))
plt.grid(True)
plt.tight_layout()

plt.savefig(
    "data/visualizations/monthly_pm10_trend.png"
)
plt.close()

print("\nHistorical EDA completed successfully!")
print("City summary saved!")
print("Monthly PM10 summary saved!")
print("Graphs saved successfully!")
