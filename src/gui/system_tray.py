from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
import os
import sys
from threading import Event

def get_resource_path(relative_path: str) -> str:
    """Get the absolute path to bundled files when using PyInstaller."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SystemMonitorTray(QSystemTrayIcon):
    """System tray icon for VitalWatch application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.stopping = Event()
        self.setup_tray()

    def setup_tray(self):
        """Setup system tray icon and menu"""
        try:
            # Check if system tray is available
            if not QSystemTrayIcon.isSystemTrayAvailable():
                print("System tray is not available on this system")
                return

            # Set icon using proper resource path
            icon_path = get_resource_path('src/icons/icon.png')
            if os.path.exists(icon_path):
                self.setIcon(QIcon(icon_path))
            else:
                # Use default system icon if custom icon not found
                if self.parent_window:
                    default_icon = self.parent_window.style().standardIcon(
                        self.parent_window.style().SP_ComputerIcon
                    )
                    self.setIcon(default_icon)
                print(f"Icon file not found: {icon_path}")

            # Create context menu
            self.create_tray_menu()

            # Set tooltip
            self.setToolTip('VitalWatch - System Monitor')
            
            # Show the tray icon
            self.show()

            # Connect the tray icon click signal
            self.activated.connect(self.on_tray_icon_activated)
            
            print("System tray icon created successfully")

        except Exception as e:
            print(f"Error setting up system tray: {e}")

    def create_tray_menu(self):
        """Create context menu for system tray"""
        menu = QMenu()

        # Show/Hide Dashboard action
        show_action = QAction("Show VitalWatch", self)
        show_action.triggered.connect(self.show_dashboard)
        menu.addAction(show_action)

        menu.addSeparator()

        # Nova Assistant action
        nova_action = QAction("Open Nova Assistant", self)
        nova_action.triggered.connect(self.open_nova_assistant)
        menu.addAction(nova_action)
    
        # Quick Stats action
        stats_action = QAction("Quick Stats", self)
        stats_action.triggered.connect(self.show_quick_stats)
        menu.addAction(stats_action)

        menu.addSeparator()

        # Exit action
        exit_action = QAction("Quit VitalWatch", self)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(exit_action)

        # Set the menu to tray icon
        self.setContextMenu(menu)
        
    def open_nova_assistant(self):
        """Open main window and switch to Nova Assistant tab"""
        if hasattr(self, 'restore_callback') and self.restore_callback:
            self.restore_callback()
        elif self.parent_window:
            self.parent_window.show()
            self.parent_window.raise_()
            self.parent_window.activateWindow()
        
        # Switch to Nova tab if possible
        if self.parent_window and hasattr(self.parent_window, 'switch_to_nova_tab'):
            self.parent_window.switch_to_nova_tab()
        
        print("Nova Assistant opened from system tray")

    def set_nova_callback(self, callback):
        """Set callback function for Nova assistant access"""
        self.nova_callback = callback

    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation events"""
        if reason == QSystemTrayIcon.Trigger:  # Single click
            self.show_dashboard()
        elif reason == QSystemTrayIcon.DoubleClick:  # Double click backup
            self.show_dashboard()

    def show_dashboard(self):
        """Show the main application window"""
        if hasattr(self, 'restore_requested'):
            self.restore_requested()
        elif self.parent_window:
            self.parent_window.show()
            self.parent_window.raise_()
            self.parent_window.activateWindow()
        print("Main window restored from system tray")

    def show_dashboard(self):
        """Show the main application window"""
        if hasattr(self, 'restore_callback') and self.restore_callback:
            self.restore_callback()
        elif self.parent_window:
            self.parent_window.show()
            self.parent_window.raise_()
            self.parent_window.activateWindow()
        print("Main window restored from system tray")

    def set_restore_callback(self, callback):
        """Set callback function for window restoration"""
        self.restore_callback = callback

    def show_quick_stats(self):
        """Show quick system statistics notification"""
        try:
            import psutil
            
            # Get current system stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            stats_message = f"CPU: {cpu_percent:.1f}% | Memory: {memory.percent:.1f}%"
            
            # Show notification
            self.showMessage(
                "VitalWatch Quick Stats",
                stats_message,
                QSystemTrayIcon.Information,
                3000  # 3 seconds
            )
            
        except Exception as e:
            print(f"Error showing quick stats: {e}")
            self.showMessage(
                "VitalWatch",
                "Unable to retrieve system stats",
                QSystemTrayIcon.Warning,
                2000
            )

    def exit_app(self):
        """Exit the application with proper cleanup"""
        try:
            self.stopping.set()
            self.hide()
            
            if hasattr(self, 'quit_requested'):
                self.quit_requested()
            else:
                QApplication.quit()
                
        except Exception as e:
            print(f"Error during application exit: {e}")
            QApplication.quit()

    def hide_tray_icon(self):
        """Hide the system tray icon"""
        self.hide()

    def show_notification(self, title, message, duration=3000):
        """Show a notification message"""
        try:
            self.showMessage(title, message, QSystemTrayIcon.Information, duration)
        except Exception as e:
            print(f"Error showing notification: {e}")