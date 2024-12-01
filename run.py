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

MAX_CSV_ROWS = 1000
OUTPUT_CSV = 'preprocess_data.csv'

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

def data_collection_task(config, stopping_event):
    """
    Periodically collect system metrics, preprocess data, and save it to a CSV file.

    Args:
        config (dict): Configuration settings.
        stopping_event (threading.Event): Event to stop the thread.
    """
    system_monitor = SystemMonitor()
    while not stopping_event.is_set():
        try:
            # Collect metrics
            metrics = [system_monitor.collect_metrics()]
            # Preprocess and append to CSV
            preprocess_data(metrics, OUTPUT_CSV)
            # Manage CSV size
            manage_csv_size(OUTPUT_CSV, MAX_CSV_ROWS)
            time.sleep(config['monitoring']['interval'])
        except Exception as e:
            print(f"Error in data collection: {e}")
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

    monitoring_thread.start()
    data_collection_thread.start()

    # Run the Qt application event loop and handle application exit
    exit_code = app.exec_()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()