from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer
import os

class SystemMonitorTray(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_tray()
        
    def setup_tray(self):
        # Set icon
        icon_path = os.path.join(os.path.dirname(__file__), '../icons/icon.jpeg')
        self.setIcon(QIcon(icon_path))
        
        # Create menu
        menu = QMenu()
        
        # Add actions
        show_action = QAction("Show Dashboard", self)
        show_action.triggered.connect(self.show_dashboard)
        menu.addAction(show_action)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(exit_action)
        
        self.setContextMenu(menu)
        self.setToolTip('System Monitor')
        self.show()
        
    def show_dashboard(self):
        if hasattr(self, 'parent') and self.parent:
            self.parent().show()
            
    def show_settings(self):
        # Implement settings dialog
        pass
        
    def exit_app(self):
        # Cleanup and exit
        QApplication.quit()
        
    def update_tooltip(self, metrics):
        tooltip = (f"CPU: {metrics['cpu']}%\n"
                  f"Memory: {metrics['memory']}%\n"
                  f"Disk: {metrics['disk']}%")
        self.setToolTip(tooltip)
    