
import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor
)
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

print("AirAssist Advanced Model Comparison started!")

# Load historical dataset
df = pd.read_csv(
    "data/processed/historical_air_quality_cleaned.csv"
)

df["Sampling Date"] = pd.to_datetime(
    df["Sampling Date"],
    dayfirst=True,
    errors="coerce"
)

df = df.dropna(
    subset=["Sampling Date", "RSPM/PM10"]
)

df = df.sort_values("Sampling Date").reset_index(drop=True)

# Create date features
df["Month"] = df["Sampling Date"].dt.month
df["DayOfYear"] = df["Sampling Date"].dt.dayofyear

# Features and target
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

# Chronological split
split_index = int(len(df) * 0.8)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

# Preprocessing
numeric_features = [
    "SO2", "NO2", "Month", "DayOfYear"
]

categorical_features = [
    "City/Town/Village/Area", "Stn Code"
]

def create_preprocessor():
    numeric_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median"))
    ])

    categorical_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ])

    return ColumnTransformer([
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features)
    ])

# Models to compare
models = {
    "Random Forest": RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        max_depth=10
    ),

    "Extra Trees": ExtraTreesRegressor(
        n_estimators=100,
        random_state=42,
        max_depth=10
    ),

    "Gradient Boosting": GradientBoostingRegressor(
        n_estimators=100,
        random_state=42,
        max_depth=3
    )
}

results = []

for name, regressor in models.items():

    pipeline = Pipeline([
        ("preprocessor", create_preprocessor()),
        ("regressor", regressor)
    ])

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(y_test, predictions) ** 0.5
    r2 = r2_score(y_test, predictions)

    results.append({
        "Model": name,
        "MAE": mae,
        "RMSE": rmse,
        "R2 Score": r2
    })

    print(f"\n{name}")
    print("MAE:", round(mae, 2))
    print("RMSE:", round(rmse, 2))
    print("R2 Score:", round(r2, 3))

# Save comparison
results_df = pd.DataFrame(results)
results_df = results_df.sort_values("MAE")

os.makedirs("data/processed", exist_ok=True)

results_df.to_csv(
    "data/processed/advanced_model_comparison.csv",
    index=False
)

print("\nFINAL MODEL COMPARISON:")
print(results_df.round(3).to_string(index=False))

print("\nComparison CSV saved!")
print("\nAirAssist Advanced Model Comparison completed!")
