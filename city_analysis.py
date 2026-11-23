
import pandas as pd
from pathlib import Path

print("AirAssist city analysis started!")

# Load cleaned dataset
df = pd.read_csv("data/processed/air_quality_cleaned.csv")

# Create city-wise pollutant summary
city_summary = df.pivot_table(
    index="city",
    columns="pollutant_id",
    values="pollutant_avg",
    aggfunc="mean"
).reset_index()

# Sort cities by PM2.5 where available
city_summary = city_summary.sort_values(
    by="PM2.5",
    ascending=False,
    na_position="last"
)

# Display first 10 cities
print("\nTOP 10 CITIES BY PM2.5:")
print(city_summary.head(10).to_string(index=False))

# Save summary
output_file = Path("data/processed/city_pollution_summary.csv")
city_summary.to_csv(output_file, index=False)

print("\nCity analysis completed!")
print("Saved:", output_file)
