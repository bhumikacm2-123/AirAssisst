
import pandas as pd
import matplotlib.pyplot as plt
import joblib
import os

print("AirAssist Error Analysis started!")

# Load cleaned historical dataset
df = pd.read_csv(
    "data/processed/historical_air_quality_cleaned.csv"
)

# Convert date column
df["Sampling Date"] = pd.to_datetime(
    df["Sampling Date"],
    dayfirst=True,
    errors="coerce"
)

# Remove records without valid dates or PM10
df = df.dropna(subset=["Sampling Date", "RSPM/PM10"])

# Sort chronologically (same approach as model training)
df = df.sort_values("Sampling Date").reset_index(drop=True)

# Create date features
df["Month"] = df["Sampling Date"].dt.month
df["DayOfYear"] = df["Sampling Date"].dt.dayofyear

# Select the same features used during training
features = [
    "SO2",
    "NO2",
    "Month",
    "DayOfYear",
    "City/Town/Village/Area",
    "Stn Code"
]

X = df[features]
y = df["RSPM/PM10"]

# Recreate chronological 80/20 test split
split_index = int(len(df) * 0.8)

X_test = X.iloc[split_index:]
y_test = y.iloc[split_index:]
test_records = df.iloc[split_index:].copy()

# Load trained model
model = joblib.load("models/pm10_random_forest.pkl")

# Predict PM10
predictions = model.predict(X_test)

# Calculate errors
results = pd.DataFrame({
    "Date": test_records["Sampling Date"].values,
    "City": test_records["City/Town/Village/Area"].values,
    "Actual_PM10": y_test.values,
    "Predicted_PM10": predictions
})

results["Error"] = (
    results["Actual_PM10"] - results["Predicted_PM10"]
)

results["Absolute_Error"] = results["Error"].abs()

print("\nFIRST 10 PREDICTIONS:")
print(results.head(10).round(2).to_string(index=False))

print("\nERROR SUMMARY:")
print("Mean Absolute Error:",
      round(results["Absolute_Error"].mean(), 2))
print("Maximum Error:",
      round(results["Absolute_Error"].max(), 2))
print("Minimum Error:",
      round(results["Absolute_Error"].min(), 2))

# City-wise error analysis
city_errors = results.groupby("City")["Absolute_Error"].mean()
city_errors = city_errors.sort_values(ascending=False)

print("\nCITY-WISE MEAN ABSOLUTE ERROR:")
print(city_errors.round(2).to_string())

# Create output folders
os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/visualizations", exist_ok=True)

# Save error results
results.to_csv(
    "data/processed/pm10_error_analysis.csv",
    index=False
)

# Plot prediction error distribution
plt.figure(figsize=(9, 5))
plt.hist(results["Error"], bins=30, edgecolor="black")
plt.xlabel("Prediction Error (Actual - Predicted)")
plt.ylabel("Number of Records")
plt.title("AirAssist PM10 Prediction Error Distribution")
plt.tight_layout()
plt.savefig("data/visualizations/pm10_error_distribution.png")
plt.close()

# Plot city-wise errors
plt.figure(figsize=(10, 6))
city_errors.sort_values().plot(kind="barh")
plt.xlabel("Mean Absolute Error")
plt.title("AirAssist PM10 Prediction Error by City")
plt.tight_layout()
plt.savefig("data/visualizations/pm10_city_errors.png")
plt.close()

print("\nError analysis CSV saved!")
print("Both error graphs saved!")
print("\nAirAssist Error Analysis completed!")
