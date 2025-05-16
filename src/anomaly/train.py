import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
import joblib

# Define column names explicitly
column_names = ["timestamp", "cpu_percent", "cpu_freq", "cpu_count_logical", 
                "cpu_load_avg_1min", "memory_used", "memory_percent", 
                "network_upload_speed", "network_download_speed"]

# Load CSV file with column names
file_path = "src/data/train_data.csv"
df = pd.read_csv(file_path, names=column_names, header=None)

# Remove timestamp column
df = df.iloc[:, 1:]

# Scale data using MinMaxScaler
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(df)

# Train Isolation Forest
model = IsolationForest(contamination=0.2, random_state=42)
model.fit(X_scaled)

# Save model and scaler
joblib.dump(model, "src/models/isolation_forest_model2.pkl")
joblib.dump(scaler, "src/models/scaler2.pkl")
print("Model and scaler saved successfully.")
