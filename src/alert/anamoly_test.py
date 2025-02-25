import os
import pandas as pd
import joblib

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALERT_DIR = os.path.join(BASE_DIR, "src", "alert")
OUTPUT_CSV = os.path.join(ALERT_DIR, 'preprocess_data.csv')
MODEL_PATH = os.path.join(ALERT_DIR, 'anomaly_model.joblib')
SCALER_PATH = os.path.join(ALERT_DIR, 'scaler.joblib')

def load_model_and_scaler():
    """
    Load the pre-trained model and scaler.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        raise FileNotFoundError("Model or scaler file not found. Please train the model first.")
    
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler

def detect_anomalies(data, model, scaler, threshold=-0.7):
    """
    Detect anomalies in the provided data using the pre-trained model and scaler.
    """
    # Preprocess the data
    X = pd.DataFrame([data])
    X_scaled = scaler.transform(X)

    # Compute anomaly scores
    scores = model.score_samples(X_scaled)

    # Check if the score is below the threshold
    is_anomaly = scores < threshold
    return is_anomaly[0], scores[0]

def simulate_anomalies():
    """
    Simulate anomalies by manually inserting data and detecting anomalies.
    """
    # Load the pre-trained model and scaler
    model, scaler = load_model_and_scaler()

    while True:
        print("\nEnter system metrics to simulate anomalies (or type 'exit' to quit):")
        cpu_usage = input("CPU Usage (%): ")
        if cpu_usage.lower() == 'exit':
            break

        memory_usage = input("Memory Usage (%): ")
        disk_io = input("Disk I/O (MB/s): ")

        try:
            # Create a dictionary with the input data
            data = {
                'cpu_usage': float(cpu_usage),
                'memory_usage': float(memory_usage),
                'disk_io': float(disk_io)
            }

            # Detect anomalies
            is_anomaly, score = detect_anomalies(data, model, scaler)

            # Print results
            if is_anomaly:
                print(f"🚨 Anomaly Detected! Score: {score:.4f}")
            else:
                print(f"✅ Normal Behavior. Score: {score:.4f}")

            # Append the data to the CSV file (optional)
            append_to_csv = input("Append this data to preprocess_data.csv? (y/n): ").lower()
            if append_to_csv == 'y':
                df = pd.DataFrame([data])
                df.to_csv(OUTPUT_CSV, mode='a', header=not os.path.exists(OUTPUT_CSV), index=False)
                print("Data appended to preprocess_data.csv.")

        except ValueError:
            print("Invalid input. Please enter numeric values.")

if __name__ == "__main__":
    simulate_anomalies()