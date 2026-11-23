
import pandas as pd

print("AirAssist monthly data coverage analysis started!")

# Load cleaned historical dataset
file_path = "data/processed/historical_air_quality_cleaned.csv"

df = pd.read_csv(file_path)

# Convert date
df["Sampling Date"] = pd.to_datetime(df["Sampling Date"])

# Extract month
df["Month"] = df["Sampling Date"].dt.month

# Count total records per month
monthly_records = df.groupby("Month").size()

print("\nTOTAL RECORDS PER MONTH:")
print(monthly_records)

# Count available PM10 measurements
monthly_pm10 = df.groupby("Month")["RSPM/PM10"].count()

print("\nAVAILABLE PM10 MEASUREMENTS PER MONTH:")
print(monthly_pm10)

# Compare monthly averages
monthly_average = df.groupby("Month")["RSPM/PM10"].mean()

print("\nMONTHLY PM10 AVERAGE:")
print(monthly_average.round(2))

print("\nMONTHLY COVERAGE ANALYSIS COMPLETED!")
