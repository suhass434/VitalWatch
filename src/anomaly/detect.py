import pandas as pd
import joblib
import sys
import os

def get_resource_path(relative_path):
    """Get the absolute path to bundled files when using PyInstaller."""
    if getattr(sys, 'frozen', False):  # Running as a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Load the pre-trained Isolation Forest model and scaler
model = joblib.load(get_resource_path("src/models/isolation_forest_model.pkl"))
scaler = joblib.load(get_resource_path("src/models/scaler.pkl"))  # Load the same MinMaxScaler

def detect_anomalies(data_file: str, THRESHOLD_STEP: int) -> pd.DataFrame:
    """
    Detect anomalies using the pre-trained Isolation Forest model.
    """
    # Define feature name mapping (excluding timestamp)
    feature_names = [
        'cpu_percent',
        'cpu_freq', 
        'cpu_count_logical',
        'cpu_load_avg_1min',
        'memory_used',
        'memory_percent',
        'network_upload_speed',
        'network_download_speed'
    ]
    
    # Load data
    df = pd.read_csv(data_file, header=None)
    
    # Remove timestamp column
    df = df.iloc[:, 1:]

    if len(df) == 0:
        print("No valid data found")
        return None
    
    # Scale the data
    X_scaled = scaler.transform(df)
    
    # Predict anomalies
    y_pred = model.predict(X_scaled)
    
    # Create DataFrame with proper column names
    df_with_names = pd.DataFrame(df.values, columns=feature_names)
    
    # Filter anomalies
    anomalies = df_with_names[y_pred == -1]
    
    if len(anomalies) > THRESHOLD_STEP * 0:
        print("Anomaly detected")
        return anomalies
    else:
        print("No anomaly detected")
        return None
        
if __name__ == "__main__":
    # Example usage
    anomalies = detect_anomalies(get_resource_path("src/data/train_data.csv"), 100)
    print(anomalies)