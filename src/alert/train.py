import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
import joblib

# Load CSV file
file_path = "src/data/train_data.csv"
df = pd.read_csv(file_path, header=None)

# Remove timestamp column (assuming the first column is a timestamp)
df = df.iloc[:, 1:]

# Scale data using MinMaxScaler
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(df)

# Train Isolation Forest
model = IsolationForest(contamination=0.2, random_state=42)
model.fit(X_scaled)

# Save model and scaler
joblib.dump(model, "src/models/isolation_forest_model.pkl")
joblib.dump(scaler, "src/models/scaler.pkl")
print("Model and scaler saved successfully.")