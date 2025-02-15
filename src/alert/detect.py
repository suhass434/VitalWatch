# src/alert/detect.py
import joblib
import pandas as pd
import numpy as np

def detect_anomalies(data_file: str, model_file: str) -> pd.DataFrame:
    """
    Detect anomalies in the provided data using a pre-trained model and scaler.
    
    Args:
        data_file (str): Path to the CSV file containing the data.
        model_file (str): Path to the trained model file.
        
    Returns:
        pd.DataFrame: DataFrame containing the detected anomalies.
    """
    # Load the model, scaler, and threshold
    model_data = joblib.load(model_file)
    model = model_data['model']
    scaler = model_data['scaler']
    threshold = model_data['threshold']
    
    # Load and preprocess data
    df = pd.read_csv(data_file)
    X = df.select_dtypes(include=['float64', 'int64'])
    
    # Scale the data using the saved scaler
    X_scaled = scaler.transform(X)
    
    # Compute anomaly scores
    scores = model.score_samples(X_scaled)
    
    # Identify anomalies (scores below the threshold)
    anomalies = df[scores < -0.7]
    
    return anomalies