
import pandas as pd
import numpy as np
import joblib

from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

print("AirAssist model comparison started!")

# Load cleaned dataset
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

# Use the same chronological split
split_index = int(len(df) * 0.8)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

# Load trained Random Forest model
rf_model = joblib.load("models/pm10_random_forest.pkl")

rf_predictions = rf_model.predict(X_test)

# Train simple baseline model
baseline = DummyRegressor(strategy="median")
baseline.fit(X_train, y_train)

baseline_predictions = baseline.predict(X_test)

# Compare evaluation metrics
for name, predictions in [
    ("Random Forest", rf_predictions),
    ("Baseline", baseline_predictions)
]:
    print(f"\n{name} RESULTS")

    print(
        "MAE:",
        round(mean_absolute_error(y_test, predictions), 2)
    )

    print(
        "RMSE:",
        round(np.sqrt(mean_squared_error(y_test, predictions)), 2)
    )

    print(
        "R2 Score:",
        round(r2_score(y_test, predictions), 3)
    )

print("\nModel comparison completed!")
