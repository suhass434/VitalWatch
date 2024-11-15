from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer
import os
from threading import Event

class SystemMonitorTray(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.stopping = Event()
        self.setup_tray()
        
    def setup_tray(self):
        # Set icon
        icon_path = os.path.join(os.path.dirname(__file__), '../icons/icon.png')
        self.setIcon(QIcon(icon_path))
        
        # Create menu
        menu = QMenu()
        
        # Add actions
        show_action = QAction("Show Dashboard", self)
        show_action.triggered.connect(self.show_dashboard)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(exit_action)
        
        self.setContextMenu(menu)
        self.setToolTip('System Monitor')
        self.show()
        
        # Connect the tray icon click signal to show the dashboard
        self.activated.connect(self.on_tray_icon_activated)
        
    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_dashboard()
            
    def show_dashboard(self):
        if self.parent_window:
            self.parent_window.show()
            self.parent_window.raise_()
            self.parent_window.activateWindow()
    
    def exit_app(self):
        self.stopping.set()
        QApplication.quit()
        
    def closeEvent(self, event):
        event.ignore()
        self.parent_window.hide()
