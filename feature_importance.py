
import pandas as pd
import matplotlib.pyplot as plt
import joblib
import os

print("AirAssist feature importance analysis started!")

# Load trained model
model = joblib.load("models/pm10_random_forest.pkl")

# Get preprocessor and Random Forest
preprocessor = model.named_steps["preprocessor"]
regressor = model.named_steps["regressor"]

# Get feature names after encoding
feature_names = preprocessor.get_feature_names_out()

# Get importance values
importance_values = regressor.feature_importances_

# Create feature importance table
importance_df = pd.DataFrame({
    "Feature": feature_names,
    "Importance": importance_values
})

# Sort from highest to lowest
importance_df = importance_df.sort_values(
    by="Importance",
    ascending=False
)

print("\nTOP 15 IMPORTANT FEATURES:")
print(importance_df.head(15).to_string(index=False))

# Save results
os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/visualizations", exist_ok=True)

importance_df.to_csv(
    "data/processed/feature_importance.csv",
    index=False
)

# Create graph
top_features = importance_df.head(15).sort_values(
    by="Importance"
)

plt.figure(figsize=(10, 7))
plt.barh(
    top_features["Feature"],
    top_features["Importance"]
)

plt.xlabel("Feature Importance")
plt.title("AirAssist PM10 Model - Feature Importance")
plt.tight_layout()

plt.savefig(
    "data/visualizations/feature_importance.png"
)

plt.close()

print("\nFeature importance CSV saved!")
print("Feature importance graph saved!")
print("\nFeature importance analysis completed!")
