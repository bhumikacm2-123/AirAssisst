
import pandas as pd

file_path = "data/raw/cpcb_dly_aq_tamil_nadu-2015.csv"

print("AirAssist historical data quality check started!")

df = pd.read_csv(file_path)

# Convert date format
df["Sampling Date"] = pd.to_datetime(
    df["Sampling Date"],
    format="%d-%m-%y",
    errors="coerce"
)

print("\n1. MISSING VALUES:")
print(df.isnull().sum())

print("\n2. DATE COVERAGE:")
print("Earliest date:", df["Sampling Date"].min())
print("Latest date:", df["Sampling Date"].max())

print("\n3. NUMBER OF CITIES:")
print(df["City/Town/Village/Area"].nunique())

print("\n4. TOP 10 CITIES:")
print(df["City/Town/Village/Area"].value_counts().head(10))

print("\n5. POLLUTANT STATISTICS:")
pollutants = ["SO2", "NO2", "RSPM/PM10", "PM 2.5"]
print(df[pollutants].describe())

print("\n6. DUPLICATE RECORDS:")
print(df.duplicated().sum())

print("\nDATA QUALITY CHECK COMPLETED!")
