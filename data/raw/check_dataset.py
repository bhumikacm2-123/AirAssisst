
from pathlib import Path

data_folder = Path("data/raw")
csv_files = list(data_folder.glob("*.csv"))

if csv_files:
    print("CSV files found:")
    for file in csv_files:
        print(file.name)
else:
    print("No CSV files found in data/raw.")
    print("Please place your air-quality CSV file inside data/raw.")

