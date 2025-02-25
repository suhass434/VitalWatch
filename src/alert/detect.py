import pandas as pd
import joblib

# Load the pre-trained Isolation Forest model and scaler
model = joblib.load("src/alert/isolation_forest_model.pkl")
scaler = joblib.load("src/alert/scaler.pkl")  # Load the same MinMaxScaler

def detect_anomalies(data_file: str, THRESHOLD_STEP: int) -> pd.DataFrame:
    """
    Detect anomalies using the pre-trained Isolation Forest model.

    Args:
        data_file (str): Path to the CSV file containing the data.

    Returns:
        pd.DataFrame: DataFrame containing the detected anomalies.
    """
    # Load data
    df = pd.read_csv(data_file, header=None)

    # Remove timestamp column
    df = df.iloc[:, 1:]

    # Scale the data using the SAME MinMaxScaler
    X_scaled = scaler.transform(df)

    # Predict anomalies (-1 = anomaly, 1 = normal)
    y_pred = model.predict(X_scaled)

    # Filter out detected anomalies
    anomalies = df[y_pred == -1]

    #print(f"Detected {len(anomalies)} anomalies")
    if (len(anomalies) > THRESHOLD_STEP / 0.8):
        print("Anomaly detected")
        return anomalies
    else:
        print("No anomaly detected")
        return None
        
if __name__ == "__main__":
    # Example usage
    anomalies = detect_anomalies("src/alert/train_data.csv", 100)
    print(anomalies)