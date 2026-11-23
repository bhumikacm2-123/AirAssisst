
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

print("AirAssist visualization started!")

# Load cleaned dataset
df = pd.read_csv("data/processed/air_quality_cleaned.csv")

# Select PM2.5 records
pm25 = df[df["pollutant_id"] == "PM2.5"].copy()

# Convert measurements to numeric
pm25["pollutant_avg"] = pd.to_numeric(
    pm25["pollutant_avg"], errors="coerce"
)

# Calculate average PM2.5 for each city
city_data = (
    pm25.groupby("city")["pollutant_avg"]
    .mean()
    .dropna()
    .sort_values(ascending=False)
    .head(10)
)

# Create graph
plt.figure(figsize=(12, 6))

city_data.sort_values().plot(
    kind="barh",
    title="Top 10 Cities by Average PM2.5 Measurement"
)

plt.xlabel("Average PM2.5 Measurement")
plt.ylabel("City")
plt.tight_layout()

# Save graph
output_folder = Path("data/visualizations")
output_folder.mkdir(parents=True, exist_ok=True)

plt.savefig(
    output_folder / "top_10_pm25_cities.png",
    dpi=300
)

print("\nGraph saved successfully!")
print("Location: data/visualizations/top_10_pm25_cities.png")

plt.show()
