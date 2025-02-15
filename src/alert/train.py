import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
import joblib
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
import logging

# Define model save path dynamically
ALERT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
MODEL_PATH = os.path.join(ALERT_DIR, "anomaly_model.pkl")
DATA_FILE = os.path.join(ALERT_DIR, "preprocess_data.csv")  # Ensure correct data path

# Ensure `alert` directory exists
os.makedirs(ALERT_DIR, exist_ok=True)

def train_model(data_file: str, model_file: str, contamination: float = 0.1, test_size: float = 0.2) -> dict:
    """
    Train an anomaly detection model on system metrics data.
    
    Args:
        data_file: Path to processed metrics CSV file
        model_file: Path to save trained model
        contamination: Expected proportion of outliers in the data
        test_size: Proportion of data to use for validation
        
    Returns:
        dict: Dictionary containing model metrics and evaluation results
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Load and prepare data
    df = pd.read_csv(data_file)
    X = df.select_dtypes(include=['float64', 'int64'])

    # Normalize the data using MinMaxScaler
    scaler = MinMaxScaler()
    X_Scaled = scaler.fit_transform(X)

    # Split data
    X_train, X_val = train_test_split(X_Scaled, test_size=test_size, random_state=42)
    
    # Add slight noise for variability
    noise = np.random.normal(0, 0.005, X_Scaled.shape)
    X_Scaled_with_noise = X_Scaled + noise

    # Train Isolation Forest model
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
        n_estimators=500,  # Increase number of trees
        max_samples=min(256, len(X_Scaled)),
        bootstrap=True
    )
    model.fit(X_Scaled_with_noise)
    
    # Compute threshold dynamically
    train_scores = model.score_samples(X_train)
    val_scores = model.score_samples(X_val)
    threshold = np.percentile(train_scores, 1)

    metrics = calculate_metrics(train_scores, val_scores, threshold)
    
    # Save model
    model_data = {
        'model': model,
        'scaler': scaler,
        'threshold': threshold
    }
    joblib.dump(model_data, model_file)

    #logging.info(f"Model saved at {model_file}")
    
    return metrics

def calculate_metrics(train_scores: np.ndarray, val_scores: np.ndarray, threshold: float) -> dict:
    """Calculate model evaluation metrics."""
    return {
        'train_mean_score': float(np.mean(train_scores)),
        'train_std_score': float(np.std(train_scores)),
        'val_mean_score': float(np.mean(val_scores)),
        'val_std_score': float(np.std(val_scores)),
        'train_anomaly_ratio': float(np.mean(train_scores < threshold)),
        'val_anomaly_ratio': float(np.mean(val_scores < threshold))
    }

if __name__ == "__main__":
    # Train the model
    metrics = train_model(
        data_file=DATA_FILE,
        model_file=MODEL_PATH,
        contamination=0.1,
        test_size=0.2
    )

    # Print metrics
    print("Training Results:")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")
