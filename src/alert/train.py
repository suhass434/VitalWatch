import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
import joblib
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
import logging

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
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    #logger = logging.getLogger(__name__)

    # Load and prepare data
    #logger.info(f"Loading data from {data_file}")
    df = pd.read_csv(data_file)
    X = df.select_dtypes(include=['float64', 'int64'])

    # Normalize the data using MinMaxScaler (scales to range 0-1)
    #logger.info("Normalizing data")
    scaler = MinMaxScaler()
    X_Scaled = scaler.fit_transform(X)

    # Split data
    #logger.info("Splitting data into train and validation sets")
    X_train, X_val = train_test_split(X_Scaled, test_size=test_size, random_state=42)
    
    # Initialize and train model
    #logger.info("Training Isolation Forest model")
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train)
    
    # Generate predictions
    #logger.info("Generating predictions")
    train_scores = model.score_samples(X_train)
    val_scores = model.score_samples(X_val)
    
    # Calculate metrics
    metrics = calculate_metrics(train_scores, val_scores)
    #logger.info(f"Model metrics: {metrics}")
    
    # Save model
    #logger.info(f"Saving model to {model_file}")
    joblib.dump(model, model_file)
    
    return metrics

def calculate_metrics(train_scores: np.ndarray, val_scores: np.ndarray) -> dict:
    """Calculate model evaluation metrics."""
    return {
        'train_mean_score': float(np.mean(train_scores)),
        'train_std_score': float(np.std(train_scores)),
        'val_mean_score': float(np.mean(val_scores)),
        'val_std_score': float(np.std(val_scores)),
        'train_anomaly_ratio': float(np.mean(train_scores < 0)),
        'val_anomaly_ratio': float(np.mean(val_scores < 0))
    }

if __name__ == "__main__":
    # Train the model
    metrics = train_model(
        data_file='preprocess_data.csv',
        model_file='anomaly_model.pkl',
        contamination=0.1,
        test_size=0.2
    )

    # Print metrics
    print("Training Results:")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")
