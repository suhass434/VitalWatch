from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, QPushButton, QLabel)

from PyQt5.QtCore import Qt
import threading

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cpu_label = QLabel("CPU Usage: --")
        self.memory_label = QLabel("Memory Usage: --")
        self.disk_label = QLabel("Disk Usage: --")
        self.setup_ui()        
        
    def setup_ui(self):
        self.setWindowTitle("AutoGuard")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Processes tab
        processes_widget = QWidget()
        tabs.addTab(processes_widget, "Processes")
        
        # Settings tab
        settings_widget = QWidget()
        tabs.addTab(settings_widget, "Settings")

        # Add labels to layout
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.memory_label)
        layout.addWidget(self.disk_label)


    def update_metrics(self, metrics):
        self.cpu_label.setText(f"CPU Usage: {metrics['cpu']['cpu_percent']}%")
        self.memory_label.setText(f"Memory Usage: {metrics['memory']['percent']}%")
        self.disk_label.setText(f"Disk Usage: {metrics['disk']['percent']}%")

    def closeEvent(self, event):
        # Minimize to tray instead of closing
        event.ignore()
        self.hide()