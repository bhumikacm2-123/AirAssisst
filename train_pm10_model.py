
import pandas as pd
import numpy as np
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

print("AirAssist PM10 Machine Learning started!")

# 1. Load cleaned historical dataset
file_path = "data/processed/historical_air_quality_cleaned.csv"
df = pd.read_csv(file_path)

# 2. Prepare date information
df["Sampling Date"] = pd.to_datetime(df["Sampling Date"])
df["Month"] = df["Sampling Date"].dt.month
df["DayOfYear"] = df["Sampling Date"].dt.dayofyear

# 3. Select input features and target
features = [
    "SO2",
    "NO2",
    "Month",
    "DayOfYear",
    "City/Town/Village/Area",
    "Stn Code"
]

target = "RSPM/PM10"

# Keep records with available PM10 values
df = df.dropna(subset=[target])

X = df[features]
y = df[target]

print("\nTotal records for modelling:", len(df))

# 4. Split chronologically: earlier records for training,
# later records for testing
df = df.sort_values("Sampling Date")
X = df[features]
y = df[target]

split_index = int(len(df) * 0.8)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

print("Training records:", len(X_train))
print("Testing records:", len(X_test))

# 5. Identify numerical and categorical columns
numeric_features = [
    "SO2", "NO2", "Month", "DayOfYear"
]

categorical_features = [
    "City/Town/Village/Area", "Stn Code"
]

# 6. Prepare preprocessing
numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median"))
])

categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer(transformers=[
    ("num", numeric_transformer, numeric_features),
    ("cat", categorical_transformer, categorical_features)
])

# 7. Create Random Forest model
model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("regressor", RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        max_depth=10
    ))
])

# 8. Train the model
print("\nTraining Random Forest model...")
model.fit(X_train, y_train)

# 9. Make predictions
predictions = model.predict(X_test)

# 10. Evaluate model
mae = mean_absolute_error(y_test, predictions)
rmse = np.sqrt(mean_squared_error(y_test, predictions))
r2 = r2_score(y_test, predictions)

print("\nMODEL EVALUATION RESULTS")
print("MAE:", round(mae, 2))
print("RMSE:", round(rmse, 2))
print("R2 Score:", round(r2, 3))

# 11. Save trained model
os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/pm10_random_forest.pkl")

print("\nModel saved successfully!")
print("Location: models/pm10_random_forest.pkl")

# 12. Show sample predictions
results = pd.DataFrame({
    "Actual PM10": y_test.values,
    "Predicted PM10": predictions
})

print("\nSAMPLE PREDICTIONS:")
print(results.head(10))

print("\nAirAssist PM10 modelling completed!")
