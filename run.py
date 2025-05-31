import sys
import os
import time
import yaml
import pandas as pd
import logging
import signal
import atexit
from threading import Thread, Event
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, Qt
from PyQt5.QtCore import QMetaObject, Q_ARG

# Import internal modules
from src.gui.main_window import MainWindow
from src.gui.system_tray import SystemMonitorTray
from src.monitors.system_monitor import SystemMonitor
from src.monitors.process_monitor import ProcessMonitor
from src.database.db import preprocess_data
from src.anomaly.detect import detect_anomalies

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_resource_path(relative_path: str) -> str:
    """Get the absolute path to bundled files when using PyInstaller."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_config() -> Dict[str, Any]:
    """
    Load configuration settings from a YAML file.
    
    Returns:
        Parsed YAML configuration data.
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    config_path = get_resource_path('config/config.yaml')
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {config_path}")
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML configuration: {e}")
        raise

def manage_csv_size(output_file: str, max_rows: int) -> int:
    """
    Efficiently manages CSV file size without loading entire file.
    
    Args:
        output_file: Path to the CSV file
        max_rows: Maximum number of rows allowed
        
    Returns:
        Number of rows in the file
    """
    if not os.path.exists(output_file):
        return 0
    
    try:
        # Use efficient line counting instead of loading all data
        with open(output_file, 'r') as f:
            row_count = sum(1 for line in f) - 1  # Subtract header
        
        if row_count > max_rows:
            # Read only the required number of lines
            df = pd.read_csv(output_file, skiprows=range(1, row_count - max_rows + 1))
            df.to_csv(output_file, index=False)
            logger.info(f"Trimmed CSV to {max_rows} rows")
            return max_rows
        
        return row_count
        
    except Exception as e:
        logger.error(f"Error managing CSV size: {e}")
        return 0

class VitalWatchApp(QObject):  # Inherit from QObject to use signals
    """Main application class that manages all components."""
    
    # Add these signals for thread-safe GUI communication
    metrics_updated = pyqtSignal(dict)
    processes_updated = pyqtSignal(list)
    anomalies_updated = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()  # Initialize QObject parent
        """Initialize the VitalWatch application."""
        self.config = load_config()
        self.stopping_event = Event()
        self.threads = []
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.tray: Optional[SystemMonitorTray] = None
        
        # Setup paths
        self.threshold_step = self.config['monitoring']['anomaly_detection_interval']
        self.alert_dir = get_resource_path("src/data")
        self.output_csv = os.path.join(self.alert_dir, 'preprocess_data.csv')
        
        # Ensure directory exists
        os.makedirs(self.alert_dir, exist_ok=True)
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.stop()
    
    def data_collection_task(self) -> None:
        """Background task for collecting system metrics."""
        system_monitor = SystemMonitor()
        logger.info("Data collection task started")
        
        while not self.stopping_event.is_set():
            try:
                # Collect metrics
                metrics = [system_monitor.collect_metrics()]
                preprocess_data(metrics, self.output_csv)
                
                # Manage CSV size
                manage_csv_size(self.output_csv, self.threshold_step)
                
                # Use event-based waiting instead of blocking sleep
                if self.stopping_event.wait(timeout=self.config['monitoring']['interval']):
                    break
                    
            except Exception as e:
                logger.error(f"Error in data collection: {e}")
                if self.stopping_event.wait(timeout=self.config['monitoring']['interval']):
                    break
        
        logger.info("Data collection task stopped")
    
    def anomaly_detection_task(self) -> None:
        iteration_count = 0
        logger.info("Anomaly detection task started")
        
        while not self.stopping_event.is_set():
            try:
                iteration_count += 1
                if iteration_count >= self.threshold_step:
                    logger.info("Executing anomaly detection cycle")
                    anomalies = detect_anomalies(self.output_csv, self.threshold_step)
                    
                    if anomalies is not None and hasattr(anomalies, 'empty') and not anomalies.empty:
                        anomaly_list = anomalies.to_dict('records')
                        QMetaObject.invokeMethod(
                            self, "anomalies_updated",
                            Qt.QueuedConnection,
                            Q_ARG(list, anomaly_list)
                        )
                        logger.info(f"Detected {len(anomalies)} anomalies")
                    else:
                        QMetaObject.invokeMethod(
                            self, "anomalies_updated", 
                            Qt.QueuedConnection,
                            Q_ARG(list, [])
                        )
                        logger.debug("No anomalies detected")
                    iteration_count = 0
                
                # ADD THIS: Wait between iterations regardless of detection
                if self.stopping_event.wait(timeout=self.config['monitoring']['interval']):
                    break
                    
            except Exception as e:
                logger.error(f"Anomaly detection failed: {e}", exc_info=True)
                self.anomalies_updated.emit([])
                # Also add delay on error
                if self.stopping_event.wait(timeout=self.config['monitoring']['interval']):
                    break

    def monitoring_task(self) -> None:
        """Background task for monitoring system metrics and updating GUI."""
        system_monitor = SystemMonitor()
        process_monitor = ProcessMonitor()
        logger.info("Monitoring task started")
        
        while not self.stopping_event.is_set():
            try:
                # Collect system metrics
                metrics = system_monitor.collect_metrics()
                # Emit signal instead of direct GUI update
                self.metrics_updated.emit(metrics)
                
                # Short wait before process update
                if self.stopping_event.wait(timeout=self.config['monitoring']['interval'] / 2):
                    break
                
                # Collect process data
                processes = process_monitor.monitor_processes()
                # Emit signal instead of direct GUI update
                self.processes_updated.emit(processes)
                
                # Wait for remaining interval
                if self.stopping_event.wait(timeout=self.config['monitoring']['interval'] / 2):
                    break
                    
            except Exception as e:
                logger.error(f"Error in monitoring: {e}")
                if self.stopping_event.wait(timeout=self.config['monitoring']['interval']):
                    break
        
        logger.info("Monitoring task stopped")
    
    def start_background_tasks(self) -> None:
        """Start all background monitoring tasks."""
        tasks = [
            ("monitoring", self.monitoring_task),
            ("data_collection", self.data_collection_task),
            ("anomaly_detection", self.anomaly_detection_task)
        ]
        
        for name, target in tasks:
            thread = Thread(target=target, name=name, daemon=True)
            thread.start()
            self.threads.append(thread)
            logger.info(f"Started {name} thread")
    
    def setup_gui(self) -> None:
        """Initialize the GUI components."""
        self.app = QApplication(sys.argv)
        
        # Prevent app from quitting when main window closes
        self.app.setQuitOnLastWindowClosed(False)
        
        # Set application icon
        icon_path = get_resource_path('src/icons/icon.png')
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
        
        # Setup main window
        self.main_window = MainWindow()
        self.main_window.show()
        
        # Connect signals to main window slots with thread-safe connections
        self.metrics_updated.connect(self.main_window.update_metrics, Qt.QueuedConnection)
        self.processes_updated.connect(self.main_window.update_process_table, Qt.QueuedConnection)
        if hasattr(self.main_window, 'update_anomaly_table'):
            self.anomalies_updated.connect(self.main_window.update_anomaly_table, Qt.QueuedConnection)
        else:
            logger.error("MainWindow does not have update_anomaly_table method")
        
        # Connect main window close event to our handler
        self.main_window.app_close_requested = self.handle_window_close
        
        # Setup system tray with proper callbacks
        self.tray = SystemMonitorTray(self.main_window)
        self.tray.set_restore_callback(self.show_from_tray)
        
        logger.info("GUI components initialized with thread-safe signal connections")

    def handle_window_close(self, should_minimize: bool) -> None:
        """Handle window close event from main window"""
        if should_minimize:
            # Hide to system tray
            self.main_window.hide()
            self.tray.show_notification(
                "VitalWatch",
                "Application minimized to system tray. Double-click tray icon to restore.",
                3000
            )
            logger.info("Application minimized to system tray")
        else:
            # Complete shutdown
            self.stop()

    def show_from_tray(self) -> None:
        """Show main window from system tray"""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            logger.info("Main window restored from system tray")

    def run(self) -> int:
        """Start the application."""
        try:
            logger.info("Starting VitalWatch application...")
            
            # Setup GUI
            self.setup_gui()
            
            # Start background tasks
            self.start_background_tasks()
            
            # Run the Qt event loop
            exit_code = self.app.exec_()
            
            logger.info(f"Application exited with code {exit_code}")
            return exit_code
            
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            return 1
        finally:
            self.cleanup()
    
    def stop(self) -> None:
        """Stop all background tasks and cleanup."""
        logger.info("Stopping application...")
        self.stopping_event.set()
        
        if self.app:
            self.app.quit()
    
    def cleanup(self) -> None:
        """Cleanup resources and wait for threads to finish."""
        if self.stopping_event.is_set():
            return  # Already cleaning up
        
        self.stopping_event.set()
        
        # Wait for all threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
                if thread.is_alive():
                    logger.warning(f"Thread {thread.name} did not stop gracefully")
        
        logger.info("Cleanup completed")

def main() -> int:
    """Main entry point for the application."""
    app = VitalWatchApp()
    return app.run()

if __name__ == '__main__':
    sys.exit(main())
