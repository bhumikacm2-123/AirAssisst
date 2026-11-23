
import pandas as pd
import os

print("AirAssist historical data cleaning started!")

# Load original historical dataset
input_file = "data/raw/cpcb_dly_aq_tamil_nadu-2015.csv"

df = pd.read_csv(input_file)

print("\nOriginal dataset shape:", df.shape)

# Remove extra spaces from text columns
for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].str.strip()

# Convert sampling date
df["Sampling Date"] = pd.to_datetime(
    df["Sampling Date"],
    format="%d-%m-%y",
    errors="coerce"
)

# Convert pollutant columns into numeric values
pollutants = ["SO2", "NO2", "RSPM/PM10", "PM 2.5"]

for col in pollutants:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove rows with invalid dates
df = df.dropna(subset=["Sampling Date"])

# Remove duplicate records
df = df.drop_duplicates()

# Keep rows if at least one pollutant measurement exists
df = df.dropna(subset=pollutants, how="all")

# Sort records by date
df = df.sort_values(by="Sampling Date")

# Create processed folder if it does not exist
os.makedirs("data/processed", exist_ok=True)

# Save cleaned historical dataset
output_file = "data/processed/historical_air_quality_cleaned.csv"

df.to_csv(output_file, index=False)

print("\nCleaned dataset shape:", df.shape)

print("\nRemaining missing values:")
print(df[pollutants].isnull().sum())

print("\nDate range:")
print(df["Sampling Date"].min())
print(df["Sampling Date"].max())

print("\nNumber of cities:", df["City/Town/Village/Area"].nunique())

print("\nHistorical data cleaning completed successfully!")
print("Saved file:", output_file)
