import sys
import os
import multiprocessing
import subprocess
import yaml
import signal
import time

from threading import Thread
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from app.gui.main_window import MainWindow
from app.gui.system_tray import SystemMonitorTray
from app.gui.styles import STYLE_SHEET
from src.monitors.system_monitor import SystemMonitor
from src.monitors.process_monitor import ProcessMonitor
from src.database.db_handler import DatabaseHandler
from src.alerts.alert_manager import AlertManager
from src.recovery.recovery_actions import RecoveryManager

def load_config():
    with open('config/config.yaml', 'r') as file:
        return yaml.safe_load(file)

def monitoring_task(main_window, config):
    # Initialize monitoring components
    system_monitor = SystemMonitor()
    #######process_monitor = ProcessMonitor()
    db_handler = DatabaseHandler()
    alert_manager = AlertManager(config)
    recovery_manager = RecoveryManager()
    
    last_backup_time = time.time()
    backup_interval = config['database']['backup_interval']

    while True:
        try:
            current_time = time.time()
            metrics = system_monitor.collect_metrics()

            # Store and update metrics
            db_handler.store_metrics(metrics)
            main_window.update_metrics(metrics)

            # Check thresholds and handle alerts
            if metrics['cpu']['cpu_percent'] > config['monitoring']['thresholds']['cpu']:
                alert_manager.send_slack_alert("High CPU Usage Detected!")
                recovery_manager.handle_high_cpu()
            
            if metrics['memory']['percent'] > config['monitoring']['thresholds']['memory']:
                alert_manager.send_slack_alert("High Memory Usage Detected!")
                recovery_manager.handle_high_memory()

            if metrics['disk']['percent'] > config['monitoring']['thresholds']['disk']:
                alert_manager.send_slack_alert("High Disk Usage Detected!")
                recovery_manager.handle_high_memory()

            if current_time - last_backup_time >= backup_interval:
                db_handler.backup_database(config['backup']['path'])
                last_backup_time = current_time

            time.sleep(config['monitoring']['interval'])
            
        except Exception as e:
            print(f"Error in monitoring loop: {str(e)}")
            time.sleep(config['monitoring']['interval'])

def process_monitoring_task(main_window, config):
    process_monitor = ProcessMonitor()

    while True:
        try:
            processes = process_monitor.monitor_processes()
            main_window.update_process_table(processes)
            time.sleep(config['monitoring']['interval'])
        
        except Exception as e:
            print(f"Error in process monitoring loop: {str(e)}")
            time.sleep(config['monitoring']['interval'])

def main():
    config = load_config()
    
    # Create Qt application
    app = QApplication(sys.argv)    # python run.py -> size = 1
    app.setStyleSheet(STYLE_SHEET)
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), 'app/icons/icon.jpeg')
    app.setWindowIcon(QIcon(icon_path))
    
    # Create main window
    main_window = MainWindow()
    main_window.show() 

    # Create system tray
    tray = SystemMonitorTray(main_window)
    
    # Start monitoring in background thread
    monitoring_thread = Thread(target=monitoring_task, args=(main_window, config), daemon=True)
    process_thread = Thread(target=process_monitoring_task, args=(main_window, config), daemon=True)
    
    monitoring_thread.start()
    process_thread.start()

    # Run the application
    exit_code = app.exec_()
    
    # Cleanup
    sys.exit(exit_code)

if __name__ == '__main__':
    main()