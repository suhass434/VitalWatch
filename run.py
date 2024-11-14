# Import necessary standard and third-party libraries
import sys
import os
import time
import yaml
from threading import Thread
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Import internal modules for GUI and monitoring tasks
from app.gui.main_window import MainWindow
from app.gui.system_tray import SystemMonitorTray
from src.monitors.system_monitor import SystemMonitor
from src.monitors.process_monitor import ProcessMonitor

def load_config():
    """
    Load configuration settings from a YAML file.
    
    Returns:
        dict: Parsed YAML configuration data.
    """
    config_path = 'config/config.yaml'
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def monitoring_task(main_window, config):
    """
    Background task to monitor system metrics and update the GUI.

    Args:
        main_window (MainWindow): Reference to the main GUI window for updating metrics.
        config (dict): Configuration settings for monitoring.
    """
    system_monitor = SystemMonitor()

    while True:
        try:
            metrics = system_monitor.collect_metrics()
            main_window.update_metrics(metrics)
            time.sleep(config['monitoring']['interval'])

        except Exception as e:
            print(f"Error in system monitoring: {e}")
            time.sleep(config['monitoring']['interval'])

def process_monitoring_task(main_window, config):
    """
    Background task to monitor processes and update the GUI's process table.

    Args:
        main_window (MainWindow): Reference to the main GUI window for updating process information.
        config (dict): Configuration settings for process monitoring.
    """
    process_monitor = ProcessMonitor()

    while True:
        try:
            processes = process_monitor.monitor_processes()
            main_window.update_process_table(processes)
            time.sleep(config['monitoring']['interval'])
        
        except Exception as e:
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
    icon_path = os.path.join(os.path.dirname(__file__), 'app/icons/icon.jpeg')
    app.setWindowIcon(QIcon(icon_path))
    
    # Setup main window and system tray icon
    main_window = MainWindow()
    main_window.show()
    tray = SystemMonitorTray(main_window)
    
    # Start monitoring tasks in separate threads
    monitoring_thread = Thread(target=monitoring_task, args=(main_window, config), daemon=True)
    process_thread = Thread(target=process_monitoring_task, args=(main_window, config), daemon=True)
    
    monitoring_thread.start()
    process_thread.start()

    # Run the Qt application event loop and handle application exit
    exit_code = app.exec_()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()