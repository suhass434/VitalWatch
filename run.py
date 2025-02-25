# Import necessary standard and third-party libraries
import sys
import os
import time
import yaml
import pandas as pd
from threading import Thread
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Import internal modules for GUI and monitoring tasks
from app.gui.main_window import MainWindow
from app.gui.system_tray import SystemMonitorTray
from src.monitors.system_monitor import SystemMonitor
from src.monitors.process_monitor import ProcessMonitor
from src.database.db import preprocess_data
from src.alert.detect import detect_anomalies

THRESHOLD_STEP = 100

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALERT_DIR = os.path.join(BASE_DIR, "src", "alert")
OUTPUT_CSV = os.path.join(ALERT_DIR, 'preprocess_data.csv')

# Ensure alert directory exists
os.makedirs(ALERT_DIR, exist_ok=True)

def load_config():
    """
    Load configuration settings from a YAML file.
    
    Returns:
        dict: Parsed YAML configuration data.
    """
    config_path = 'config/config.yaml'
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def manage_csv_size(output_file, max_rows):
    """
    Ensures the CSV file does not exceed the specified number of rows.

    Args:
        output_file (str): Path to the CSV file.
        max_rows (int): Maximum number of rows allowed in the CSV file.
    """
    if os.path.exists(output_file):
        df = pd.read_csv(output_file)
        if len(df) > max_rows:
            df = df.iloc[-max_rows:]  # Keep only the last `max_rows` rows
            df.to_csv(output_file, index=False)
        return len(df)
    return 0

def data_collection_task(config, stopping_event):
    system_monitor = SystemMonitor()

    while not stopping_event.is_set():
        try:
            # Collect metrics
            metrics = [system_monitor.collect_metrics()]
            preprocess_data(metrics, OUTPUT_CSV)

            # Manage CSV size
            manage_csv_size(OUTPUT_CSV, THRESHOLD_STEP)  
            
            # Wait before collecting the next data point
            time.sleep(config['monitoring']['interval'])

        except Exception as e:
            print(f"Error in data collection task: {e}")
            time.sleep(config['monitoring']['interval'])

def anomaly_detection_task(config, stopping_event, main_window):
    """Background task to detect anomalies and update the UI"""
    iteration_count = 0

    while not stopping_event.is_set():
        try:
            iteration_count += 1
            
            if iteration_count >= THRESHOLD_STEP:
                print("It's time to run a system check and detect any anomalies!")
                # Detect anomalies and update UI
                anomalies = detect_anomalies(OUTPUT_CSV, THRESHOLD_STEP)
                main_window.update_anomaly_table(anomalies)
                iteration_count = 0  # Reset counter
                
            time.sleep(config['monitoring']['interval'])

        except Exception as e:
            print(f"Error in anomaly detection task: {e}")
            time.sleep(config['monitoring']['interval'])

def monitoring_task(main_window, config, stopping_event):
    """
    Background task to monitor system metrics and update the GUI.

    Args:
        main_window (MainWindow): Reference to the main GUI window for updating metrics.
        config (dict): Configuration settings for monitoring.
    """
    system_monitor = SystemMonitor()
    process_monitor = ProcessMonitor()

    while not stopping_event.is_set():
        try:
            metrics = system_monitor.collect_metrics()
            main_window.update_metrics(metrics)
            time.sleep(config['monitoring']['interval'])
            processes = process_monitor.monitor_processes()
            main_window.update_process_table(processes)
            time.sleep(config['monitoring']['interval'])

        except Exception as e:
            print(f"Error in system monitoring: {e}")
            time.sleep(config['monitoring']['interval'])
            print(f"Error in process monitoring: {e}")
            time.sleep(config['monitoring']['interval'])

def main():
    """
    Main function to initialize and start the application.
    """
    # Load configuration data
    config = load_config()
    
    # Initialize Qt application
    app = QApplication(sys.argv)
    icon_path = os.path.join(os.path.dirname(__file__), 'app/icons/icon.png')
    app.setWindowIcon(QIcon(icon_path))
    
    # Setup main window and system tray icon
    main_window = MainWindow()
    main_window.show()
    tray = SystemMonitorTray(main_window)
    
    # Start monitoring tasks in separate threads
    monitoring_thread = Thread(target=monitoring_task, args=(main_window, config, tray.stopping), daemon=True)
    data_collection_thread = Thread(target=data_collection_task, args=(config, tray.stopping), daemon=True)
    anomaly_detection_thread = Thread(target=anomaly_detection_task, args=(config, tray.stopping, main_window), daemon=True)

    monitoring_thread.start()
    data_collection_thread.start()
    anomaly_detection_thread.start()

    # Run the Qt application event loop and handle application exit
    exit_code = app.exec_()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()