
import pandas as pd
from pathlib import Path

print("AirAssist cleaning started!")

# Read original CSV
df = pd.read_csv("data/raw/Air Assist.csv")

print("Original dataset:", df.shape)

# Remove duplicate rows
df = df.drop_duplicates()

# Convert numeric columns
columns = [
    "latitude",
    "longitude",
    "pollutant_min",
    "pollutant_max",
    "pollutant_avg"
]

for col in columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove rows with missing essential values
df = df.dropna(
    subset=["city", "pollutant_id", "pollutant_avg"]
)

# Save cleaned dataset
output_folder = Path("data/processed")
output_folder.mkdir(parents=True, exist_ok=True)

df.to_csv(
    output_folder / "air_quality_cleaned.csv",
    index=False
)

print("Cleaned dataset:", df.shape)
print("Cleaning completed successfully!")
