
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

print("PM10 visualization started!")

# Load cleaned data
df = pd.read_csv("data/processed/air_quality_cleaned.csv")

# Select PM10 measurements
pm10 = df[df["pollutant_id"] == "PM10"].copy()

# Calculate city-wise average
city_data = (
    pm10.groupby("city")["pollutant_avg"]
    .mean()
    .dropna()
    .sort_values(ascending=False)
    .head(10)
)

# Draw horizontal bar chart
plt.figure(figsize=(12, 6))

city_data.sort_values().plot(
    kind="barh",
    title="Top 10 Cities by Average PM10 Measurement"
)

plt.xlabel("Average PM10 Measurement")
plt.ylabel("City")
plt.tight_layout()

# Save graph
output_folder = Path("data/visualizations")
output_folder.mkdir(parents=True, exist_ok=True)

plt.savefig(
    output_folder / "top_10_pm10_cities.png",
    dpi=300
)

print("PM10 graph saved successfully!")

plt.show()
