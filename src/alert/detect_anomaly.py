import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib

def detect_anomalies(data_file, model_file):
    """
    Detect anomalies in the provided dataset using a pre-trained Isolation Forest model.

    Args:
        data_file (str): Path to the CSV file containing preprocessed data.
        model_file (str): Path to the pre-trained Isolation Forest model file.

    Returns:
        pd.DataFrame: DataFrame containing rows flagged as anomalies.
    """
    try:
        # Load pre-trained Isolation Forest model
        model = joblib.load(model_file)
        
        # Load and preprocess new data
        df = pd.read_csv(data_file)
        X = df.select_dtypes(include=['float64', 'int64'])
        
        # Scale features
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Anomaly detection
        scores = model.score_samples(X_scaled)
        predictions = model.predict(X_scaled)
        
        # Append results to the dataset
        df['anomaly_score'] = scores
        df['anomaly'] = predictions
        
        # Filter anomalies
        anomalies = df[df['anomaly'] == -1]

        return anomalies
    
    except Exception as e:
        print(f"Error during anomaly detection: {e}")
        return pd.DataFrame()  # Return empty DataFrame if an error occurs
