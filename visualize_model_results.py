
import pandas as pd
import matplotlib.pyplot as plt
import joblib
import os

print("AirAssist model visualization started!")

# Load dataset
df = pd.read_csv(
    "data/processed/historical_air_quality_cleaned.csv"
)

df["Sampling Date"] = pd.to_datetime(df["Sampling Date"])
df["Month"] = df["Sampling Date"].dt.month
df["DayOfYear"] = df["Sampling Date"].dt.dayofyear

features = [
    "SO2", "NO2", "Month", "DayOfYear",
    "City/Town/Village/Area", "Stn Code"
]

target = "RSPM/PM10"

df = df.dropna(subset=[target])
df = df.sort_values("Sampling Date")

X = df[features]
y = df[target]

# Same chronological train-test split
split_index = int(len(df) * 0.8)

X_test = X.iloc[split_index:]
y_test = y.iloc[split_index:]

# Load trained model
model = joblib.load("models/pm10_random_forest.pkl")

predictions = model.predict(X_test)

# Create visualization folder
os.makedirs("data/visualizations", exist_ok=True)

# Graph 1: Actual vs Predicted
plt.figure(figsize=(8, 6))

plt.scatter(y_test, predictions, alpha=0.6)

minimum = min(y_test.min(), predictions.min())
maximum = max(y_test.max(), predictions.max())

plt.plot(
    [minimum, maximum],
    [minimum, maximum],
    linestyle="--"
)

plt.xlabel("Actual PM10")
plt.ylabel("Predicted PM10")
plt.title("Actual vs Predicted PM10")

plt.tight_layout()
plt.savefig(
    "data/visualizations/actual_vs_predicted.png"
)
plt.close()

# Graph 2: Prediction errors
errors = y_test.values - predictions

plt.figure(figsize=(8, 6))
plt.scatter(predictions, errors, alpha=0.6)
plt.axhline(y=0, linestyle="--")

plt.xlabel("Predicted PM10")
plt.ylabel("Prediction Error")
plt.title("PM10 Prediction Error Analysis")

plt.tight_layout()
plt.savefig(
    "data/visualizations/pm10_prediction_errors.png"
)
plt.close()

print("\nBoth graphs saved successfully!")
print("Actual vs Predicted graph created!")
print("Prediction error graph created!")
print("\nAirAssist visualization completed!")
