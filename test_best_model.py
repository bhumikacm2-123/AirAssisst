
import joblib
import pandas as pd

print("AirAssist Best Model Testing started!")

# Load saved model
model = joblib.load("models/best_pm10_model.pkl")

# Example input
sample_data = pd.DataFrame({
    "SO2": [12.0],
    "NO2": [25.0],
    "Month": [11],
    "DayOfYear": [315],
    "City/Town/Village/Area": ["Chennai"],
    "Stn Code": [768]
})

# Generate prediction
prediction = model.predict(sample_data)

print("\nSAMPLE INPUT:")
print(sample_data.to_string(index=False))

print("\nPREDICTED PM10 VALUE:")
print(round(prediction[0], 2))

print("\nModel testing completed successfully!")

