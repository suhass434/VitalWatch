import pandas as pd
import logging
import os
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
from src.monitors.system_monitor import SystemMonitor

def preprocess_data(metrics, output_file, fill_missing=True, default_value=0):
    """
    Preprocess system metrics data collected from the SystemMonitor.
    
    Args:
        metrics (list[dict]): List of dictionaries containing system metrics
        output_file (str): Path to output CSV file
        fill_missing (bool): Whether to fill or drop missing values
        default_value (int): Default value for filling missing data
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Extract relevant fields for training
    data = []
    for metric in metrics:
        timestamp = metric['timestamp']
        cpu_metrics = metric['cpu']
        memory_metrics = metric['memory']
        network_metrics = metric['network']
        
        # Select specific features for training
        row = {
            'timestamp': timestamp,
            'cpu_percent': cpu_metrics.get('cpu_percent', None),
            'cpu_freq': cpu_metrics.get('cpu_freq', None),
            'cpu_count_logical': cpu_metrics.get('cpu_count_logical', None),
            'cpu_load_avg_1min': cpu_metrics.get('cpu_load_avg_1min', None),
            'memory_used': memory_metrics.get('used', None),
            'memory_percent': memory_metrics.get('percent', None),
            'network_upload_speed': network_metrics.get('upload_speed', None),
            'network_download_speed': network_metrics.get('download_speed', None)
        }
        data.append(row)
    
    # Convert metrics list to a DataFrame
    df = pd.DataFrame(data)
    
    # Handle missing values
    if fill_missing:
        df = df.fillna(default_value)
    else:
        df = df.dropna()
    
    # Convert timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # # Normalize numerical columns
    # numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
    # if len(numeric_columns) > 0:
    #     # Initialize MinMaxScaler
    #     scaler = MinMaxScaler()
        
    #     for column in numeric_columns:
    #         # Normalize all numerical columns, even if they have the same values
    #         df[[column]] = scaler.fit_transform(df[[column]].values.reshape(-1, 1))
    #         logger.info(f"Normalized column: {column}")
    # else:
    #     logger.warning("No numerical columns found for normalization")

    # Save processed data
    if os.path.exists(output_file):
        #logger.info(f"Appending processed data to {output_file}")
        df.to_csv(output_file, mode='a', header=False, index=True)
    else:
        #logger.info(f"Creating new file and saving processed data to {output_file}")
        df.to_csv(output_file, index=True)
        
    return df

if __name__ == '__main__':
    # Sample usage
    system_monitor = SystemMonitor()
    
    # Collect metrics (e.g., for 5 snapshots)
    metrics = []
    for _ in range(5):
        metrics.append(system_monitor.collect_metrics())
    
    # Preprocess and save to CSV
    preprocess_data(metrics, 'preprocess_data.csv')
