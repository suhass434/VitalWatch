import asyncio
import os
import sys
import tempfile
import threading
import time
from typing import Dict, Any, Optional, List
import yaml
import pandas as pd
import edge_tts
import subprocess
import concurrent.futures
import speech_recognition as sr
from PyQt5.QtCore import pyqtSlot

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QTabWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
    QHeaderView, QGroupBox, QCheckBox, QButtonGroup, QRadioButton, 
    QApplication, QGraphicsOpacityEffect, QLineEdit, QTextEdit, 
    QDialog, QListWidget, QListWidgetItem, QMessageBox, QSystemTrayIcon,
    QMenu, QAction, QSizePolicy
)

from PyQt5.QtCore import Qt, QSize, QThread, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QMovie, QPixmap, QBrush, QPen, QFont, QPainter, QIcon
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis

from src.gui.styleSheet import STYLE_SHEET
from src.assistant.detect_os import get_os_distro
from src.anomaly.detect import detect_anomalies
from src.assistant.llm_client import query_llm, summarize_output
from src.assistant.parser import parse_response
from src.assistant.executor import is_safe, execute
import src.assistant.config
from src.gui.system_tray import SystemMonitorTray

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
        Parsed YAML configuration data
    """
    config_path = get_resource_path('config/config.yaml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

class NovaWorker(QObject):
    """Worker class for Nova assistant commands"""
    status_update = pyqtSignal(str)
    state_update = pyqtSignal(str)
    message_update = pyqtSignal(str, str)
    speak_signal = pyqtSignal(str)
    finished = pyqtSignal()
    confirmation_needed = pyqtSignal(dict, str, str)
    execute_command_signal = pyqtSignal(dict)

    def __init__(self, user_input: str, os_distro: str, use_safe_flag: bool, force_confirm: bool, voice_mode):
        super().__init__()
        self.user_input = user_input
        self.os_distro = os_distro
        self.USE_SAFE_FLAG = use_safe_flag
        self.FORCE_CONFIRM = force_confirm
        self.voice_mode = voice_mode

        # Connect the execute signal to the method
        self.execute_command_signal.connect(self._execute_command)

    def process_command(self) -> None:
        """Process user command without blocking the UI"""
        self.status_update.emit("Processing your request...")
        self.state_update.emit("processing")
        
        # Use QTimer to make API call non-blocking
        QTimer.singleShot(0, self._query_llm_async)

    def _query_llm_async(self):
        """Make LLM API call in a non-blocking way"""
        try:
            # Use ThreadPoolExecutor for the network call
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(query_llm, self.user_input, self.os_distro)
                # Set a reasonable timeout
                raw = future.result(timeout=10)  # 10 second timeout
                
            # Parse response
            QTimer.singleShot(0, lambda: self._parse_response_async(raw))
            
        except Exception as e:
            response = f"Error connecting to Nova: {e}"
            self.message_update.emit("Nova", response)
            self.state_update.emit("error")
            self.speak_signal.emit(response)
            self.finished.emit()

    def _parse_response_async(self, raw: str):
        """Parse LLM response asynchronously"""
        try:
            cmd = parse_response(raw)
            
            # Handle command or conversation
            if cmd["type"] == "command":
                self._handle_command(cmd)
            elif cmd["type"] == "conversation":
                self._handle_conversation(cmd)
                
        except ValueError as e:
            response = f"Error parsing response: {e}"
            self.message_update.emit("Nova", response)
            self.speak_signal.emit(response)
            self.state_update.emit("error")
            self.finished.emit()
    
    def _handle_command(self, cmd: Dict[str, Any]) -> None:
        """Handle command execution"""
        if self.USE_SAFE_FLAG and not is_safe(cmd):
            response = "Sorry, that command is not allowed for security reasons."
            self.message_update.emit("Nova", response)
            self.speak_signal.emit(response)
            self.state_update.emit("error")
            self.finished.emit()
            return

        if self.FORCE_CONFIRM:
            self.status_update.emit("Waiting for confirmation...")
            self.state_update.emit("idle")
            self.confirmation_needed.emit(cmd, self.os_distro, self.user_input)
            return
        
        self.status_update.emit("Executing command...")
        self._execute_command(cmd)
    
    def _handle_conversation(self, cmd: Dict[str, Any]) -> None:
        """Handle conversation response"""
        self.message_update.emit("Nova", cmd["response"])
        self.state_update.emit("speaking")

        if self.voice_mode:
            # Don't emit ready status - let TTS handle it
            self.speak_signal.emit(cmd["response"])
        else:
            # No TTS, so we can reset status immediately
            self.speak_signal.emit(cmd["response"])
            self.status_update.emit("Nova is ready. Type a command or question.")
        self.finished.emit()
        
    def _execute_command(self, cmd: Dict[str, Any]) -> None:
        """Execute the actual command asynchronously"""
        # Use QTimer for non-blocking execution
        QTimer.singleShot(0, lambda: self._run_command_async(cmd))

    def _run_command_async(self, cmd: Dict[str, Any]):
        """Run command in background without blocking"""
        try: 
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Execute command with timeout
                future = executor.submit(execute, cmd)
                result = future.result(timeout=15)  # 15 second timeout
                
                # Process result
                if result:
                    # Make summary generation async too
                    QTimer.singleShot(0, lambda: self._generate_summary_async(result, cmd))
                else:
                    response = "Command executed successfully."
                    self.message_update.emit("Nova", response)
                    self.state_update.emit("speaking")
                    self.status_update.emit("Ready")
                    self.speak_signal.emit(response)
                    self.finished.emit()
                    
        except Exception as e:
            response = f"Error executing command: {e}"
            self.message_update.emit("Nova", response)
            self.state_update.emit("error")
            self.speak_signal.emit(response)
            self.finished.emit()

    def _generate_summary_async(self, result: str, cmd: Dict[str, Any]):
        """Generate summary asynchronously"""
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    summarize_output,
                    self.user_input,
                    cmd["target"],
                    result,
                    self.os_distro
                )
                summary = future.result(timeout=8)
                
                self.message_update.emit("Nova", summary)
                self.state_update.emit("speaking")
                
                if self.voice_mode:
                    # Let TTS handle status updates
                    self.speak_signal.emit(summary)
                else:
                    # No TTS, reset status immediately
                    self.speak_signal.emit(summary)
                    self.status_update.emit("Nova is ready. Type a command or question.")
                    
        except Exception as e:
            response = f"Command completed. Result: {result[:200]}..."
            self.message_update.emit("Nova", response)
            self.state_update.emit("speaking")
            
            if self.voice_mode:
                self.speak_signal.emit(response)
            else:
                self.speak_signal.emit(response)
                self.status_update.emit("Nova is ready. Type a command or question.")
        finally:
            self.finished.emit()

class MainWindow(QMainWindow):
    """Main application window for VitalWatch"""
    voice_input_received = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self._init_properties()
        self._init_ui_components()
        self.setup_ui()

    def _init_properties(self) -> None:
        """Initialize window properties"""
        self.font_size = 10
        self.font = QFont("Arial", self.font_size)
        self.setFont(self.font)
        
        # State variables
        self.VOICE_MODE = False
        self.is_speaking = False
        self.speech_event = threading.Event()
        self.speech_event.set()
        self._was_listening = False 

        # Configuration
        self.os_distro = get_os_distro()
        self.USE_SAFE_FLAG = True
        self.FORCE_CONFIRM = True
        
        # Data tracking
        self.current_processes: List[Dict[str, Any]] = []
        self.data_points = 0
        self.max_data_points = 50
        self.show_all_processes = False

        # Anomaly detection configuration
        self.THRESHOLD_STEP = self.config['monitoring']['anomaly_detection_interval']
        self.OUTPUT_CSV = get_resource_path("src/data/preprocess_data.csv")
    
        # Add this line for chat history
        self.chat_history = []

        # Audio tracking
        self.audio_process = None
        self.is_audio_playing = False
        self.VOICE_INPUT_MODE = False
        self.recognizer = None
        self.microphone = None
        self.is_listening = False  # Track if actively listening
        self.stop_listening_callback = None  # Reference to voice thread
        self.voice_input_received.connect(self.handle_voice_input)

        os.makedirs(os.path.dirname(self.OUTPUT_CSV), exist_ok=True)

    def _init_ui_components(self) -> None:
        """Initialize UI components"""
        # Labels
        self.cpu_percent = QLabel("CPU Usage: --")
        self.memory_label = QLabel("Memory Usage: --")
        self.disk_label = QLabel("Disk Usage: --")
        self.network_label = QLabel("Network Usage: --")
        
        # Chart series
        self.cpu_series = QLineSeries()
        self.memory_series = QLineSeries()
        self.disk_series = QLineSeries()
        self.network_upload_series = QLineSeries()
        self.network_download_series = QLineSeries()
        
        # Charts
        self.cpu_chart = QChart()
        self.memory_chart = QChart()
        self.disk_chart = QChart()
        self.network_chart = QChart()

    def setup_assistant_animation(self) -> None:
        """Set up the assistant animation once - runs continuously"""
        try:
            gif_path = get_resource_path("assets/animations/nova_idle.gif")
            
            if os.path.exists(gif_path):
                movie = QMovie(gif_path)
                movie.setScaledSize(QSize(160, 160))
                movie.start()
                
                if hasattr(self, 'assistant_icon'):
                    self.assistant_icon.setMovie(movie)
                    self._assistant_movie = movie
                    print("Assistant animation loaded successfully")
            else:
                print(f"Animation file not found: {gif_path}")
                if hasattr(self, 'assistant_icon'):
                    self.assistant_icon.setText("Nova")
                    
        except Exception as e:
            print(f"Error loading assistant animation: {e}")
            if hasattr(self, 'assistant_icon'):
                self.assistant_icon.setText("Nova")

    def run_anomaly_detection(self) -> None:
        """Run anomaly detection manually"""
        try:
            self.anomaly_status.setText("Running anomaly detection...")
            self.detect_button.setEnabled(False)
            
            # Simulate detection (replace with actual detection logic)
            anomalies = detect_anomalies(self.OUTPUT_CSV, self.THRESHOLD_STEP)
            
            if anomalies is not None :
                self.update_anomaly_table(anomalies)
                self.anomaly_status.setText(f"Detection complete. Found {len(anomalies)} anomalies.")
            else:
                self.anomaly_status.setText("Detection complete. No anomalies found.")
            
            # Update last run time
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.last_run_time.setText(f"Last run: {current_time}")
            
        except Exception as e:
            self.anomaly_status.setText(f"Detection failed: {e}")
        finally:
            self.detect_button.setEnabled(True)

    def set_dark_mode(self) -> None:
        """Set dark mode theme"""
        if hasattr(self, 'dark_button') and self.dark_button.isChecked():
            self.set_theme('dark')
            self.fix_tab_sizing() 

    def set_light_mode(self) -> None:
        """Set light mode theme"""
        if hasattr(self, 'light_button') and self.light_button.isChecked():
            self.set_theme('light')
            self.fix_tab_sizing() 

    def fix_tab_sizing(self):
        """Force tab widget to recalculate size after font/theme changes"""
        if hasattr(self, 'tabs'):
            # Force font metric recalculation
            self.tabs.setFont(self.tabs.font())
            # Clear cached size hints
            self.tabs.updateGeometry()
            # Process font change events
            QApplication.processEvents()
            # Resize to optimal size
            self.tabs.adjustSize()
            self.adjustSize()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration - wrapper for module function"""
        return load_config()

    def speak_text(self, text: str) -> None:
        """Non-blocking TTS using QTimer"""
        if not self.VOICE_MODE:
            return
        
        # Pause voice input to prevent the assistant from hearing itself
        if self.VOICE_INPUT_MODE and self.is_listening:
            self.stop_voice_listening()
            self._was_listening = True
        else:
            self._was_listening = False
        
        # Show stop button when speaking starts
        self.nova_status.setText("Speaking...")   
        self.stop_audio_button.show()

        # Use QTimer.singleShot for non-blocking execution
        QTimer.singleShot(0, lambda: self._speak_in_background(text))
    
    def _speak_in_background(self, text: str):
        """Run TTS in background without blocking"""
        try:
            # Generate TTS file
            async def generate_tts():
                communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
                tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                await communicate.save(tmp_audio.name)
                return tmp_audio.name
            
            # Run async TTS generation in thread pool
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, generate_tts())
                audio_file = future.result(timeout=5)  # 5 second timeout
                
                # Play audio and track process
                self.audio_process = subprocess.Popen(['play', audio_file], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
                
                # Monitor when audio finishes
                QTimer.singleShot(100, self._check_audio_finished)
                
        except Exception as e:
            print(f"TTS Error: {e}")
            self._reset_audio_ui()

    def _check_audio_finished(self):
        """Check if audio playback has finished"""
        if self.audio_process and self.audio_process.poll() is None:
            # Still playing, check again
            QTimer.singleShot(100, self._check_audio_finished)
        else:
            # Audio finished
            self._reset_audio_ui()

    def stop_audio(self):
        """Stop audio playback"""
        if self.audio_process and self.audio_process.poll() is None:
            self.audio_process.terminate()
        self._reset_audio_ui()

    def _reset_audio_ui(self):
        """Reset audio UI elements"""
        self.stop_audio_button.hide()
        self.audio_process = None
        self.is_audio_playing = False

        # Restart listening if it was paused for speech
        if self.VOICE_INPUT_MODE and getattr(self, '_was_listening', False):
            self._was_listening = False  # Reset the flag
            self.nova_status.setText("Resuming listening...")
            QTimer.singleShot(250, self.start_voice_listening) # Restart after a short delay
        elif self.VOICE_INPUT_MODE:
            self.nova_status.setText("Voice input active")
        else:
            self.nova_status.setText("Nova is ready. Type a command or question.")

    def toggle_voice_mode(self, enable: bool) -> None:
        """
        Toggle voice output mode for text-to-speech functionality
        """
        self.VOICE_MODE = enable

        if enable:
            if hasattr(self, 'nova_status'):
                self.nova_status.setText("Text-to-speech enabled")
            self.add_nova_message("System", "Voice commands coming soon. Text-to-speech works now!")
        else:
            if hasattr(self, 'nova_status'):
                self.nova_status.setText("Voice mode disabled")

    def send_nova_command(self) -> None:
        """Send a command to Nova assistant using thread-safe approach"""
        user_input = self.nova_input.text().strip()
        if not user_input:
            return

        self.nova_input.clear()
        self.add_nova_message("You", user_input)

        # Clean up previous thread safely
        self._cleanup_nova_thread()

        # Create worker and thread
        self.nova_thread = QThread()
        self.nova_worker = NovaWorker(
            user_input, self.os_distro, self.USE_SAFE_FLAG, self.FORCE_CONFIRM, self.VOICE_MODE
        )
        self.nova_worker.moveToThread(self.nova_thread)

        # Connect signals with Qt.QueuedConnection for thread safety
        self.nova_worker.status_update.connect(self.nova_status.setText, Qt.QueuedConnection)
        self.nova_worker.state_update.connect(self.set_assistant_state, Qt.QueuedConnection)
        self.nova_worker.message_update.connect(self.add_nova_message, Qt.QueuedConnection)
        self.nova_worker.speak_signal.connect(self.speak_text, Qt.QueuedConnection)
        self.nova_worker.confirmation_needed.connect(self.handle_command_confirmation, Qt.QueuedConnection)

        # Connect cleanup signals
        self.nova_worker.finished.connect(self._cleanup_nova_thread, Qt.QueuedConnection)

        # Start processing
        self.nova_thread.started.connect(self.nova_worker.process_command)
        self.nova_thread.start()

    def _cleanup_nova_thread(self) -> None:
        """Safely cleanup Nova thread and worker"""
        if hasattr(self, 'nova_thread') and self.nova_thread is not None:
            try:
                if self.nova_thread.isRunning():
                    self.nova_thread.quit()
                    self.nova_thread.wait(2000)
            except RuntimeError:
                # Object already deleted
                pass
            finally:
                self.nova_thread = None
        
        if hasattr(self, 'nova_worker'):
            self.nova_worker = None

    def handle_command_confirmation(self, cmd: Dict[str, Any], os_distro: str, user_input: str) -> None:
        """Handle command confirmation dialog - non-blocking version"""
        reply = QMessageBox.question(
            self, 'Confirm Command',
            f"Execute {cmd['action']} → {cmd['target']}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Set status immediately
            self.nova_status.setText("Executing command...")
            
            # Execute in background to prevent UI freezing
            QTimer.singleShot(0, lambda: self._execute_confirmed_command_async(cmd, os_distro, user_input))
        else:
            response = "Command cancelled."
            self.add_nova_message("Nova", response)
            self.speak_text(response)
            self.nova_status.setText("Nova is ready. Type a command or question.")
    def _execute_confirmed_command_async(self, cmd: Dict[str, Any], os_distro: str, user_input: str) -> None:
        """Execute confirmed command in background thread"""
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Execute command with timeout
                future = executor.submit(execute, cmd)
                result = future.result(timeout=15)  # 15 second timeout
                
                if result:
                    # Generate summary in background too
                    QTimer.singleShot(0, lambda: self._generate_confirmed_summary_async(result, cmd, user_input, os_distro))
                else:
                    response = "Command executed successfully."
                    self.add_nova_message("Nova", response)
                    # Set speaking status BEFORE calling speak_text
                    self.nova_status.setText("Speaking...")
                    self.speak_text(response)
                    
        except Exception as e:
            response = f"Error executing command: {e}"
            self.add_nova_message("Nova", response)
            self.nova_status.setText("Speaking...")
            self.speak_text(response)

    def _generate_confirmed_summary_async(self, result: str, cmd: Dict[str, Any], user_input: str, os_distro: str) -> None:
        """Generate summary for confirmed command execution"""
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    summarize_output,
                    user_input,
                    cmd["target"],
                    result,
                    os_distro
                )
                summary = future.result(timeout=8)  # 8 second timeout
                
                self.add_nova_message("Nova", summary)
                # Set speaking status BEFORE calling speak_text
                self.nova_status.setText("Speaking...")
                self.speak_text(summary)
                
        except Exception as e:
            # Fallback to raw result
            response = f"Command completed. Result: {result[:200]}..."
            self.add_nova_message("Nova", response)
            self.nova_status.setText("Speaking...")
            self.speak_text(response)

    def set_assistant_state(self, state: str) -> None:
        """Set the assistant animation state"""
        valid_states = ["idle", "processing", "speaking", "error"]
        if state not in valid_states:
            state = "idle"
        
        # Store current state
        self._current_assistant_state = state
        
        # Update assistant icon based on state (if needed)
        # For simple continuous animation, this might not be necessary

    def add_nova_message(self, source: str, message: str) -> None:
        """Add a message to the Nova conversation display with text color only"""
        timestamp = time.strftime("%H:%M:%S")
        colors = STYLE_SHEET['dark' if hasattr(self, 'dark_button') and self.dark_button.isChecked() else 'light']
        
        # Store in history (add this block)
        history_entry = {
            'timestamp': timestamp,
            'source': source,
            'message': message,
            'full_timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.chat_history.append(history_entry)

        # Set text colors without background fills
        if source == "You":
            text_color = "#4A90E2"  # Blue for user messages
        elif source == "System":
            text_color = "#FFA500"  # Orange for system messages
        else:  # Nova
            text_color = "#00C851"  # Green for Nova messages
        
        # Format message with text color only, no background
        formatted_message = f'''
        <div style="margin: 10px 0; padding: 5px;">
            <div style="color: {text_color}; padding: 4px; word-wrap: break-word;">
                <strong>{source}</strong> <span style="color: gray; font-size: 11px;">[{timestamp}]</span><br>
                <span style="color: {colors['text_color']};">{message}</span>
            </div>
        </div>
        '''
        
        if hasattr(self, 'nova_conversation'):
            self.nova_conversation.append(formatted_message)
            
            # Auto-scroll to bottom
            scrollbar = self.nova_conversation.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def show_nova_history(self) -> None:
        """Show Nova conversation history in a dialog"""
        if not self.chat_history:
            QMessageBox.information(self, "History", "No conversation history found.")
            return
        
        # Create history dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Nova Chat History")
        dialog.setModal(True)
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # History display
        history_text = QTextEdit()
        history_text.setReadOnly(True)
        
        # Format history
        for entry in self.chat_history:
            source_color = "#4A90E2" if entry['source'] == "You" else "#00C851" if entry['source'] == "Nova" else "#FFA500"
            history_html = f'''
            <div style="margin: 5px 0; padding: 3px;">
                <span style="color: {source_color}; font-weight: bold;">{entry['source']}</span>
                <span style="color: gray; font-size: 10px;"> [{entry['full_timestamp']}]</span><br>
                <span style="margin-left: 10px;">{entry['message']}</span>
            </div>
            '''
            history_text.append(history_html)
        
        layout.addWidget(history_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear History")
        clear_button.clicked.connect(lambda: self.clear_chat_history(dialog))
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        
        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        dialog.exec_()

    def clear_chat_history(self, dialog=None) -> None:
        """Clear the chat history"""
        reply = QMessageBox.question(
            self,
            'Clear History',
            'Are you sure you want to clear all chat history?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.add_nova_message("System", "Chat history cleared.")
            self.chat_history.clear()
            if dialog:
                dialog.accept()

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update UI metrics without blocking"""
        try:
            # Update labels
            cpu_data = metrics.get('cpu', {})
            memory_data = metrics.get('memory', {})
            disk_data = metrics.get('disk', {})
            network_data = metrics.get('network', {})
            
            self.cpu_percent.setText(f"CPU Usage: {cpu_data.get('cpu_percent', '--')}%")
            self.memory_label.setText(f"Memory Usage: {memory_data.get('percent', '--')}%")
            self.disk_label.setText(f"Disk Usage: {disk_data.get('percent', '--')}%")
            
            # Update network with proper formatting
            upload = network_data.get('upload_speed', 0)
            download = network_data.get('download_speed', 0)

            # Create HTML with colored text to indicate line meanings
            network_html = f'''
            <span style="color: #FF6384;">↑ Upload: {upload:.1f} KB/s</span> | 
            <span style="color: #36A2EB;">↓ Download: {download:.1f} KB/s</span>
            '''
            self.network_label.setText(network_html)

            # Update charts
            self._update_charts(metrics)
            
            # Update detailed tables
            self._update_detail_tables(metrics)
            
        except Exception as e:
            print(f"Error updating metrics: {e}")
    
    def _update_charts(self, metrics: Dict[str, Any]) -> None:
        """Add new data points to chart series and update display ranges for scrolling effect"""
        try:
            # Convert metric values to numeric format for charting
            cpu_percent = float(metrics.get('cpu', {}).get('cpu_percent', 0))
            memory_percent = float(metrics.get('memory', {}).get('percent', 0))
            disk_percent = float(metrics.get('disk', {}).get('percent', 0))
            
            # Get both upload and download speeds
            upload_speed = float(metrics.get('network', {}).get('upload_speed', 0)) / 1024  # KB/s
            download_speed = float(metrics.get('network', {}).get('download_speed', 0)) / 1024  # KB/s
            
            # Add current data points to each chart series
            self.cpu_series.append(self.data_points, cpu_percent)
            self.memory_series.append(self.data_points, memory_percent)
            self.disk_series.append(self.data_points, disk_percent)
            
            # Add data points to both network series
            self.network_upload_series.append(self.data_points, upload_speed)
            self.network_download_series.append(self.data_points, download_speed)
            
            # Create scrolling window effect by updating X-axis range
            if self.data_points >= self.max_data_points:
                # Calculate the visible window range for recent data
                start_range = self.data_points - self.max_data_points + 1
                end_range = self.data_points + 1
                
                # Update X-axis range for all charts to show recent data window
                for chart in [self.cpu_chart, self.memory_chart, self.disk_chart, self.network_chart]:
                    x_axis = chart.axisX()
                    if x_axis:
                        x_axis.setRange(start_range, end_range)
            
            # Remove oldest data points to maintain performance and memory usage
            if self.cpu_series.count() > self.max_data_points:
                self.cpu_series.removePoints(0, 1)
                self.memory_series.removePoints(0, 1)
                self.disk_series.removePoints(0, 1)
                
                # Remove points from both network series
                self.network_upload_series.removePoints(0, 1)
                self.network_download_series.removePoints(0, 1)
            
            # Dynamically adjust network chart Y-axis based on both upload and download data
            if hasattr(self, 'network_chart'):
                network_y_axis = self.network_chart.axisY()
                if network_y_axis and (self.network_upload_series.count() > 0 or self.network_download_series.count() > 0):
                    # Get all network speed values from both series
                    all_speeds = []
                    
                    # Collect upload speeds
                    for i in range(self.network_upload_series.count()):
                        all_speeds.append(self.network_upload_series.at(i).y())
                    
                    # Collect download speeds
                    for i in range(self.network_download_series.count()):
                        all_speeds.append(self.network_download_series.at(i).y())
                    
                    if all_speeds:
                        max_speed = max(all_speeds)
                        # Set Y range with padding above maximum value
                        network_y_axis.setRange(0, max(max_speed * 1.2, 100))
            
            # Increment counter for next data point
            self.data_points += 1
            
            # Force Qt to redraw all charts with updated ranges and data
            for chart in [self.cpu_chart, self.memory_chart, self.disk_chart, self.network_chart]:
                chart.update()
                
            #print(f"Charts updated: CPU={cpu_percent}%, Memory={memory_percent}%, Upload={upload_speed:.1f}KB/s, Download={download_speed:.1f}KB/s")
            
        except Exception as e:
            print(f"Error updating charts: {e}")

    def _apply_chart_borders(self) -> None:
        """Apply professional borders to all chart views"""
        chart_views = []
        if hasattr(self, 'cpu_chart_view'): chart_views.append(self.cpu_chart_view)
        if hasattr(self, 'memory_chart_view'): chart_views.append(self.memory_chart_view)
        if hasattr(self, 'disk_chart_view'): chart_views.append(self.disk_chart_view)
        if hasattr(self, 'network_chart_view'): chart_views.append(self.network_chart_view)
        
        for view in chart_views:
            if view:
                view.setStyleSheet("""
                    QChartView {
                        border: 2px solid #CCCCCC;
                        border-radius: 8px;
                        background-color: white;
                    }
                """)

    def _update_detail_tables(self, metrics: Dict[str, Any]) -> None:
        """Update detailed metric tables"""
        try:
            # Update CPU table
            cpu_data = metrics.get('cpu', {})
            if hasattr(self, 'cpu_table'):
                cpu_items = [
                    f"{cpu_data.get('cpu_percent', '--')}%",
                    f"{cpu_data.get('cpu_freq', '--')} MHz",
                    f"{cpu_data.get('cpu_count_logical', '--')}",
                    f"{cpu_data.get('cpu_count_physical', '--')}",
                    f"{cpu_data.get('cpu_load_avg_1min', '--')}",
                    f"{cpu_data.get('cpu_context_switches', '--')}",
                    f"{cpu_data.get('cpu_interrupts', '--')}",
                    f"{cpu_data.get('cpu_syscalls', '--')}",
                    f"{cpu_data.get('cpu_user_time', '--')}s",
                    f"{cpu_data.get('cpu_system_time', '--')}s",
                    f"{cpu_data.get('cpu_idle_time', '--')}s",
                    f"{cpu_data.get('cpu_temp', '--')}°C"
                ]
                
                for i, item in enumerate(cpu_items):
                    if i < self.cpu_table.rowCount():
                        self.cpu_table.setItem(i, 1, QTableWidgetItem(item))

            # Update Memory table
            memory_data = metrics.get('memory', {})
            if hasattr(self, 'memory_table'):
                def format_bytes(bytes_val):
                    if bytes_val == '--' or bytes_val is None:
                        return '--'
                    try:
                        gb = bytes_val / (1024**3)
                        if gb > 1:
                            return f"{gb:.2f} GB"
                        else:
                            return f"{bytes_val / (1024**2):.2f} MB"
                    except:
                        return str(bytes_val)

                memory_items = [
                    format_bytes(memory_data.get('total', '--')),
                    format_bytes(memory_data.get('available', '--')),
                    f"{memory_data.get('percent', '--')}%",
                    format_bytes(memory_data.get('used', '--')),
                    format_bytes(memory_data.get('swap_total', '--')),
                    format_bytes(memory_data.get('swap_used', '--')),
                    format_bytes(memory_data.get('swap_free', '--')),
                    f"{memory_data.get('swap_percent', '--')}%"
                ]
                
                for i, item in enumerate(memory_items):
                    if i < self.memory_table.rowCount():
                        self.memory_table.setItem(i, 1, QTableWidgetItem(item))

            # Update Disk table
            disk_data = metrics.get('disk', {})
            if hasattr(self, 'disk_table'):
                disk_items = [
                    format_bytes(disk_data.get('total', '--')),
                    format_bytes(disk_data.get('used', '--')),
                    format_bytes(disk_data.get('free', '--')),
                    f"{disk_data.get('percent', '--')}%",
                    f"{disk_data.get('read_count', '--')}",
                    f"{disk_data.get('write_count', '--')}",
                    format_bytes(disk_data.get('read_bytes', '--')),
                    format_bytes(disk_data.get('write_bytes', '--')),
                    f"{disk_data.get('read_time', '--')}ms",
                    f"{disk_data.get('write_time', '--')}ms"
                ]
                
                for i, item in enumerate(disk_items):
                    if i < self.disk_table.rowCount():
                        self.disk_table.setItem(i, 1, QTableWidgetItem(item))

            # Update Network table
            network_data = metrics.get('network', {})
            if hasattr(self, 'network_table'):
                network_items = [
                    f"{network_data.get('upload_speed', 0):.1f} KB/s",
                    f"{network_data.get('download_speed', 0):.1f} KB/s",
                    format_bytes(network_data.get('total_data_sent', '--')),
                    format_bytes(network_data.get('total_data_received', '--'))
                ]
                
                for i, item in enumerate(network_items):
                    if i < self.network_table.rowCount():
                        self.network_table.setItem(i, 1, QTableWidgetItem(item))

            # Update Battery table
            battery_data = metrics.get('battery', {})
            if hasattr(self, 'battery_table'):
                if isinstance(battery_data, dict):
                    battery_items = [
                        f"{battery_data.get('battery_percentage', '--')}%",
                        battery_data.get('status', '--'),
                        battery_data.get('time_remaining', '--')
                    ]
                else:
                    battery_items = [str(battery_data), '--', '--']
                
                for i, item in enumerate(battery_items):
                    if i < self.battery_table.rowCount():
                        self.battery_table.setItem(i, 1, QTableWidgetItem(item))

        except Exception as e:
            print(f"Error updating detail tables: {e}")

    def update_process_table(self, processes: List[Dict[str, Any]]) -> None:
        """Update process table without blocking"""
        try:
            self.current_processes = processes
            
            if hasattr(self, 'process_table'):
                # Limit processes if not showing all
                display_processes = processes if self.show_all_processes else processes[:20]
                
                self.process_table.setRowCount(len(display_processes))
                
                for row, process in enumerate(display_processes):
                    self.process_table.setItem(row, 0, QTableWidgetItem(str(process.get('pid', '--'))))
                    self.process_table.setItem(row, 1, QTableWidgetItem(process.get('name', '--')))
                    self.process_table.setItem(row, 2, QTableWidgetItem(process.get('status', '--')))
                    self.process_table.setItem(row, 3, QTableWidgetItem(f"{process.get('cpu_percent', 0):.1f}%"))
                    self.process_table.setItem(row, 4, QTableWidgetItem(f"{process.get('memory_percent', 0):.1f}%"))
                    self.process_table.setItem(row, 5, QTableWidgetItem(process.get('create_time', '--')))
                    
        except Exception as e:
            print(f"Error updating process table: {e}")

    def update_anomaly_table(self, anomalies: list) -> None:
        """Update the anomaly detection table with new results"""
        try:
            if hasattr(self, 'anomaly_table'):
                self.anomaly_table.setRowCount(len(anomalies))
                
                for row, anomaly in enumerate(anomalies):
                    for col, (key, value) in enumerate(anomaly.items()):
                        item = QTableWidgetItem(str(value))
                        self.anomaly_table.setItem(row, col, item)
                
                # Update status
                if hasattr(self, 'anomaly_status'):
                    if anomalies:
                        self.anomaly_status.setText(f"Found {len(anomalies)} anomalies")
                    else:
                        self.anomaly_status.setText("No anomalies detected")
                
                # Update timestamp
                if hasattr(self, 'last_run_time'):
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    self.last_run_time.setText(f"Last run: {current_time}")
                    
        except Exception as e:
            logger.error(f"Error updating anomaly table: {e}")

    def toggle_process_view(self) -> None:
        """Toggle between showing all processes or limited view"""
        self.show_all_processes = not self.show_all_processes
        if hasattr(self, 'show_all_button'):
            self.show_all_button.setText("Show Less" if self.show_all_processes else "Show More")
        # Trigger table update with current data
        self.update_process_table(self.current_processes)

    def toggle_nova_voice_mode(self) -> None:
        """Toggle speech output mode"""
        self.VOICE_MODE = not self.VOICE_MODE
        if hasattr(self, 'speech_output_button'):
            # Update button appearance instead of text
            if self.VOICE_MODE:
                self.speech_output_button.setStyleSheet("background-color: #00C851; color: white;")
            else:
                self.speech_output_button.setStyleSheet("")
        
        status = "enabled" if self.VOICE_MODE else "disabled"
        self.add_nova_message("System", f"Speech output {status}.")

    def toggle_command_confirmation(self, state: bool) -> None:
        """Toggle whether commands require confirmation before execution"""
        self.FORCE_CONFIRM = state
        status = "enabled" if state else "disabled"
        self.add_nova_message("System", f"Command confirmation {status}.")

    def set_dark_mode(self) -> None:
        """Set dark mode theme"""
        self.set_theme('dark')

    def set_light_mode(self) -> None:
        """Set light mode theme"""
        self.set_theme('light')

    def set_theme(self, mode: str = 'dark') -> None:
        """Apply comprehensive theme styling to all application components"""
        colors = STYLE_SHEET[mode]
        
        # Apply comprehensive stylesheet covering all widgets
        comprehensive_stylesheet = f"""
            QMainWindow {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
            }}
            
            QWidget {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {colors['border_color']};
                background-color: {colors['background_color']};
            }}
            
            QTabBar::tab {{
                background-color: {colors['grid_color']};
                color: {colors['text_color']};
                padding: 8px 20px;
                border: 1px solid {colors['border_color']};
                border-bottom: none;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
                border-bottom: 1px solid {colors['background_color']};
                font-weight: bold;
            }}
            
            QTabBar::tab:hover {{
                background-color: {colors.get('hover_color', colors['border_color'])};
            }}

            QTextEdit {{
                background-color: {colors['nova_bg']};
                color: {colors['nova_text']};
                border: 1px solid {colors['border_color']};
                border-radius: 8px;
                padding: 8px;
            }}
            
            QLineEdit {{
                background-color: {colors['input_bg']};
                color: {colors['input_text']};
                border: 1px solid {colors['border_color']};
                padding: 8px;
                border-radius: 4px;
            }}
            
            QLabel {{
                color: {colors['label_text_color']};
                background-color: transparent;
                border: none;
                padding: 5px;
            }}
            
            QPushButton {{
                background-color: {colors.get('button_bg', colors['grid_color'])};
                color: {colors.get('button_text', colors['text_color'])};
                border: 1px solid {colors['border_color']};
                padding: 8px 16px;
                border-radius: 4px;
                font-size: {self.font_size}pt;
            }}
            
            QPushButton:hover {{
                background-color: {colors.get('button_hover', colors['background_color'])};
            }}
            
            QTableWidget {{
                background-color: {colors['table_background']};
                color: {colors['table_text_color']};
                gridline-color: {colors['border_color']};
                border: 1px solid {colors['border_color']};
                selection-background-color: transparent;
            }}
            
            QTableWidget::item {{
                background-color: {colors['table_background']};
                color: {colors['table_text_color']};
                padding: 4px;
            }}
            
            QHeaderView::section {{
                background-color: {colors['grid_color']};
                color: {colors['text_color']};
                padding: 8px;
                border: 1px solid {colors['border_color']};
                font-weight: bold;
            }}
            
            QGroupBox {{
                color: {colors['text_color']};
                border: 2px solid {colors['border_color']};
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
                font-size: {self.font_size}pt;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {colors['text_color']};
                background-color: {colors['background_color']};
            }}
            
            QCheckBox, QRadioButton {{
                color: {colors['text_color']};
                spacing: 8px;
                font-size: {self.font_size}pt;
            }}
        """
        
        # Apply the stylesheet
        self.setStyleSheet(comprehensive_stylesheet)
        
        # Update chart themes with proper colors
        self._update_chart_themes(mode, colors)
        
        print(f"Applied {mode} theme to all application components including charts")

    def _update_chart_themes(self, mode: str, colors: dict) -> None:
        """Update chart background colors and pen colors for current theme"""
        try:
            # Define chart colors based on theme mode
            if mode == 'dark':
                chart_bg_color = QColor(43, 43, 43)  # Dark background
                chart_text_color = QColor(255, 255, 255)  # White text
                plot_area_color = QColor(60, 60, 60)  # Slightly lighter plot area
                grid_color = QColor(128, 128, 128, 100)  # Semi-transparent gray
                border_color = QColor(100, 100, 100)

                # Dark mode pen colors
                cpu_pen_color = QColor(255, 99, 71)     # Tomato red
                memory_pen_color = QColor(75, 192, 192) # Teal
                disk_pen_color = QColor(138, 43, 226)  # Purple
                upload_pen_color = QColor(255, 99, 132) # Pink
                download_pen_color = QColor(54, 162, 235) # Blue
            else:
                chart_bg_color = QColor(255, 255, 255)  # Light background
                chart_text_color = QColor(0, 0, 0)      # Black text
                plot_area_color = QColor(248, 248, 248) # Light gray plot area
                grid_color = QColor(200, 200, 200, 150) # Light gray grid
                border_color = QColor(180, 180, 180)

                # Light mode pen colors (darker for visibility)
                cpu_pen_color = QColor(220, 53, 69)     # Dark red
                memory_pen_color = QColor(40, 167, 69)  # Dark green
                disk_pen_color = QColor(138, 43, 226)  # Purple 
                upload_pen_color = QColor(220, 53, 69)  # Dark red
                download_pen_color = QColor(0, 123, 255) # Bright blue
            
            # Update chart backgrounds and axes
            charts = [self.cpu_chart, self.memory_chart, self.disk_chart, self.network_chart]
            
            for chart in charts:
                if chart:
                    # Set chart and plot area backgrounds
                    chart.setBackgroundBrush(QBrush(chart_bg_color))
                    chart.setPlotAreaBackgroundBrush(QBrush(plot_area_color))
                    chart.setPlotAreaBackgroundVisible(True)
                    
                    # Update title
                    chart.setTitleBrush(QBrush(chart_text_color))
                    
                    # Update axes colors
                    if chart.axisX():
                        chart.axisX().setLabelsColor(chart_text_color)
                        chart.axisX().setTitleBrush(QBrush(chart_text_color))
                        chart.axisX().setLinePenColor(chart_text_color)
                        chart.axisX().setGridLineColor(grid_color)
                    
                    if chart.axisY():
                        chart.axisY().setLabelsColor(chart_text_color)
                        chart.axisY().setTitleBrush(QBrush(chart_text_color))
                        chart.axisY().setLinePenColor(chart_text_color)
                        chart.axisY().setGridLineColor(grid_color)
            
            # Update series pen colors with theme-appropriate colors
            self._update_series_colors(cpu_pen_color, memory_pen_color, disk_pen_color, 
                                    upload_pen_color, download_pen_color)
            
            # Update chart view backgrounds
            chart_views = []
            if hasattr(self, 'cpu_chart_view'): chart_views.append(self.cpu_chart_view)
            if hasattr(self, 'memory_chart_view'): chart_views.append(self.memory_chart_view)
            if hasattr(self, 'disk_chart_view'): chart_views.append(self.disk_chart_view)
            if hasattr(self, 'network_chart_view'): chart_views.append(self.network_chart_view)
            
            for view in chart_views:
                if view:
                    view.setBackgroundBrush(QBrush(chart_bg_color))
            
            print(f"Chart themes updated for {mode} mode")
            
        except Exception as e:
            print(f"Error updating chart themes: {e}")

    def _update_series_colors(self, cpu_color: QColor, memory_color: QColor, disk_color: QColor,
                            upload_color: QColor, download_color: QColor) -> None:
        """Update series pen colors"""
        try:
            # Update CPU series color
            if hasattr(self, 'cpu_series'):
                cpu_pen = self.cpu_series.pen()
                cpu_pen.setColor(cpu_color)
                cpu_pen.setWidth(2)
                self.cpu_series.setPen(cpu_pen)
            
            # Update Memory series color
            if hasattr(self, 'memory_series'):
                memory_pen = self.memory_series.pen()
                memory_pen.setColor(memory_color)
                memory_pen.setWidth(2)
                self.memory_series.setPen(memory_pen)
            
            # Update Disk series color
            if hasattr(self, 'disk_series'):
                disk_pen = self.disk_series.pen()
                disk_pen.setColor(disk_color)
                disk_pen.setWidth(2)
                self.disk_series.setPen(disk_pen)
            
            # Update Network series colors
            if hasattr(self, 'network_upload_series'):
                upload_pen = self.network_upload_series.pen()
                upload_pen.setColor(upload_color)
                upload_pen.setWidth(2)
                self.network_upload_series.setPen(upload_pen)
            
            if hasattr(self, 'network_download_series'):
                download_pen = self.network_download_series.pen()
                download_pen.setColor(download_color)
                download_pen.setWidth(2)
                self.network_download_series.setPen(download_pen)
                
        except Exception as e:
            print(f"Error updating series colors: {e}")

    def load_config(self) -> Dict[str, Any]:
        """Load configuration - wrapper for module function"""
        return load_config()

    def setup_ui(self) -> None:
        """Setup the complete UI"""
        self.setWindowTitle("VitalWatch - System Monitor")
        self.setGeometry(100, 100, 1230, 864)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Setup all tabs
        self._setup_overview_tab(self.tabs)
        self._setup_nova_tab(self.tabs)
        self._setup_detail_tabs(self.tabs)
        self._setup_processes_tab(self.tabs)
        self._setup_anomaly_tab(self.tabs)
        self._setup_settings_tab(self.tabs)
        
        # Apply default theme
        self.set_dark_mode()
        
        # Setup assistant animation
        self.setup_assistant_animation()

    def _setup_overview_tab(self, tabs: QTabWidget) -> None:
        """Create overview tab with system metrics labels positioned directly above their charts"""
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        
        # Create main container for all metric+chart pairs
        main_container = QWidget()
        main_layout = QGridLayout(main_container)
        main_layout.setSpacing(8)  # Responsive spacing
        main_layout.setContentsMargins(10, 10, 10, 10)  # Consistent margins
        
        # Configure charts before creating views
        self._setup_charts()
        
        # Create CPU metric container with label above chart
        cpu_container = QWidget()
        cpu_container.setMinimumSize(250, 180)  # Set minimum container size
        cpu_layout = QVBoxLayout(cpu_container)
        cpu_layout.setContentsMargins(3, 3, 3, 3)  # Reduced margins
        cpu_layout.setSpacing(3)
        
        self.cpu_percent.setAlignment(Qt.AlignCenter)
        cpu_layout.addWidget(self.cpu_percent)
        
        self.cpu_chart_view = QChartView(self.cpu_chart)
        self.cpu_chart_view.setRenderHint(QPainter.Antialiasing)
        # Remove fixed minimum height, use size policy instead
        self.cpu_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        cpu_layout.addWidget(self.cpu_chart_view)
        
        # Create Memory metric container with label above chart
        memory_container = QWidget()
        memory_container.setMinimumSize(250, 180)  # Set minimum container size
        memory_layout = QVBoxLayout(memory_container)
        memory_layout.setContentsMargins(3, 3, 3, 3)  # Reduced margins
        memory_layout.setSpacing(3)
        
        self.memory_label.setAlignment(Qt.AlignCenter)
        memory_layout.addWidget(self.memory_label)
        
        self.memory_chart_view = QChartView(self.memory_chart)
        self.memory_chart_view.setRenderHint(QPainter.Antialiasing)
        # Remove fixed minimum height, use size policy instead
        self.memory_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        memory_layout.addWidget(self.memory_chart_view)
        
        # Create Disk metric container with label above chart
        disk_container = QWidget()
        disk_container.setMinimumSize(250, 180)  # Set minimum container size
        disk_layout = QVBoxLayout(disk_container)
        disk_layout.setContentsMargins(3, 3, 3, 3)  # Reduced margins
        disk_layout.setSpacing(3)
        
        self.disk_label.setAlignment(Qt.AlignCenter)
        disk_layout.addWidget(self.disk_label)
        
        self.disk_chart_view = QChartView(self.disk_chart)
        self.disk_chart_view.setRenderHint(QPainter.Antialiasing)
        # Remove fixed minimum height, use size policy instead
        self.disk_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        disk_layout.addWidget(self.disk_chart_view)
        
        # Create Network metric container with label above chart
        network_container = QWidget()
        network_container.setMinimumSize(250, 180)  # Set minimum container size
        network_layout = QVBoxLayout(network_container)
        network_layout.setContentsMargins(3, 3, 3, 3)  # Reduced margins
        network_layout.setSpacing(3)
        
        self.network_label.setAlignment(Qt.AlignCenter)
        network_layout.addWidget(self.network_label)
        
        self.network_chart_view = QChartView(self.network_chart)
        self.network_chart_view.setRenderHint(QPainter.Antialiasing)
        # Remove fixed minimum height, use size policy instead
        self.network_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        network_layout.addWidget(self.network_chart_view)
        
        # Arrange metric containers in 2x2 grid layout
        main_layout.addWidget(cpu_container, 0, 0)
        main_layout.addWidget(memory_container, 0, 1)
        main_layout.addWidget(disk_container, 1, 0)
        main_layout.addWidget(network_container, 1, 1)
        
        # Set equal column and row stretching for balanced layout
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        main_layout.setRowStretch(0, 1)
        main_layout.setRowStretch(1, 1)
        
        # Set minimum size for the main container
        main_container.setMinimumSize(520, 380)
        
        overview_layout.addWidget(main_container)
        self.tabs.addTab(overview_widget, "Overview")

        # Apply borders after all chart views are created
        self._apply_chart_borders()

        print("Overview tab created with responsive chart sizing")

    def _setup_charts(self) -> None:
        """Configure chart objects with proper axes and series attachments"""
        # Setup CPU, Memory, and Disk charts (single series each)
        single_series_charts = [
            (self.cpu_chart, self.cpu_series, "CPU Usage (%)", "Time", "Usage %", 100, QColor(255, 99, 71)),
            (self.memory_chart, self.memory_series, "Memory Usage (%)", "Time", "Usage %", 100, QColor(75, 192, 192)),
            (self.disk_chart, self.disk_series, "Disk Usage (%)", "Time", "Usage %", 100, QColor(255, 205, 86))
        ]
        
        for chart, series, title, x_label, y_label, y_max, color in single_series_charts:
            # Remove any existing series to prevent conflicts
            chart.removeAllSeries()
            
            # Add the data series to the chart
            chart.addSeries(series)
            chart.setTitle(title)
            chart.legend().hide()
            
            # Set series color
            pen = series.pen()
            pen.setColor(color)
            pen.setWidth(2)
            series.setPen(pen)
            
            # Create X-axis for time-based data points
            axis_x = QValueAxis()
            axis_x.setTitleText(x_label)
            axis_x.setLabelFormat("%d")
            axis_x.setRange(0, self.max_data_points)
            axis_x.setTickCount(5)
            
            # Create Y-axis for metric values
            axis_y = QValueAxis()
            axis_y.setTitleText(y_label)
            axis_y.setLabelFormat("%.1f")
            axis_y.setRange(0, y_max)
            axis_y.setTickCount(6)
            
            # Attach axes to chart and link series to axes
            chart.addAxis(axis_x, Qt.AlignBottom)
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
            
            # Disable animations for real-time performance
            chart.setAnimationOptions(QChart.NoAnimation)
        
        # Setup Network chart with dual series (upload and download)
        self.network_chart.removeAllSeries()
        
        # Add both upload and download series
        self.network_chart.addSeries(self.network_upload_series)
        self.network_chart.addSeries(self.network_download_series)
        self.network_chart.setTitle("Network Speed (KB/s)")
        self.network_chart.legend().hide()  # Hide legend
        
        # Configure upload series appearance (red color)
        upload_pen = self.network_upload_series.pen()
        upload_pen.setColor(QColor(255, 99, 132))  # Red
        upload_pen.setWidth(2)
        self.network_upload_series.setPen(upload_pen)
        self.network_upload_series.setName("Upload Speed")
        
        # Configure download series appearance (blue color)
        download_pen = self.network_download_series.pen()
        download_pen.setColor(QColor(54, 162, 235))  # Blue
        download_pen.setWidth(2)
        self.network_download_series.setPen(download_pen)
        self.network_download_series.setName("Download Speed")
        
        # Create axes for network chart
        network_axis_x = QValueAxis()
        network_axis_x.setTitleText("Time")
        network_axis_x.setLabelFormat("%d")
        network_axis_x.setRange(0, self.max_data_points)
        network_axis_x.setTickCount(5)
        
        network_axis_y = QValueAxis()
        network_axis_y.setTitleText("Speed (KB/s)")
        network_axis_y.setLabelFormat("%.1f")
        network_axis_y.setRange(0, 1000)  # Initial range, will be adjusted dynamically
        network_axis_y.setTickCount(6)
        
        # Attach axes to chart and link both series to same axes
        self.network_chart.addAxis(network_axis_x, Qt.AlignBottom)
        self.network_chart.addAxis(network_axis_y, Qt.AlignLeft)
        
        # Attach both series to the same axes
        self.network_upload_series.attachAxis(network_axis_x)
        self.network_upload_series.attachAxis(network_axis_y)
        self.network_download_series.attachAxis(network_axis_x)
        self.network_download_series.attachAxis(network_axis_y)
        
        # Disable animations for real-time performance
        self.network_chart.setAnimationOptions(QChart.NoAnimation)
        
        print("Charts configured with proper axes and dual network series")

    def _setup_nova_tab(self, tabs: QTabWidget) -> None:
        """Setup Nova assistant tab"""
        nova_widget = QWidget()
        nova_layout = QVBoxLayout(nova_widget)
        
        # Nova title
        nova_title = QLabel("Nova Virtual Assistant")
        nova_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        nova_title.setAlignment(Qt.AlignCenter)
        
        # Nova description
        nova_description = QLabel("Nova is an intelligent system-command assistant that can help you with system tasks and answer questions.")
        nova_description.setWordWrap(True)
        nova_description.setAlignment(Qt.AlignCenter)
        
        # Assistant icon container
        feedback_container = QWidget()
        feedback_layout = QVBoxLayout(feedback_container)
        feedback_layout.setAlignment(Qt.AlignCenter)

        self.assistant_icon = QLabel()
        self.assistant_icon.setAlignment(Qt.AlignCenter)
        self.assistant_icon.setFixedSize(160, 160)
        self.assistant_icon.setStyleSheet("border: none;")  # Remove any borders
        feedback_layout.addWidget(self.assistant_icon, 0, Qt.AlignCenter)  # Center in layout
                
        # Conversation display
        self.nova_conversation = QTextEdit()
        self.nova_conversation.setReadOnly(True)
        self.nova_conversation.setMinimumHeight(300)
        
        # Input controls
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        
        self.nova_input = QLineEdit()
        self.nova_input.setPlaceholderText("Type your command or question here...")
        self.nova_input.returnPressed.connect(self.send_nova_command)
        
        self.nova_send_button = QPushButton("Send")
        self.nova_send_button.clicked.connect(self.send_nova_command)
        
        self.speech_output_button = QPushButton("Speech Output")
        self.speech_output_button.clicked.connect(self.toggle_nova_voice_mode)
        
        self.microphone_button = QPushButton("Microphone")
        self.microphone_button.setObjectName("voiceInputButton")
        self.microphone_button.clicked.connect(self.toggle_voice_input_mode)

        self.nova_history_button = QPushButton("History")
        self.nova_history_button.clicked.connect(self.show_nova_history)
        
        input_layout.addWidget(self.nova_input)
        input_layout.addWidget(self.nova_send_button)
        input_layout.addWidget(self.speech_output_button)
        input_layout.addWidget(self.microphone_button)
        input_layout.addWidget(self.nova_history_button)
        
        # Status container with stop button
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)  # Add spacing between elements

        self.nova_status = QLabel("Nova is ready. Type a command or question.")
        self.nova_status.setAlignment(Qt.AlignCenter)

        # Stop button with proper size
        self.stop_audio_button = QPushButton("Stop")
        self.stop_audio_button.setFixedSize(70, 30)  # Increased size
        self.stop_audio_button.clicked.connect(self.stop_audio)
        self.stop_audio_button.hide()

        # Add widgets with stretch to control positioning
        status_layout.addStretch(1)  # Push everything to center
        status_layout.addWidget(self.nova_status)
        status_layout.addWidget(self.stop_audio_button)  # Right next to status
        status_layout.addStretch(1)  # Balance the layout

        # Add to layout
        nova_layout.addWidget(status_container)
        
        # Add to layout
        nova_layout.addWidget(nova_title)
        nova_layout.addWidget(nova_description)
        nova_layout.addWidget(feedback_container)
        nova_layout.addWidget(self.nova_conversation)
        nova_layout.addWidget(input_container)
        nova_layout.addWidget(status_container)
        
        self.tabs.addTab(nova_widget, "Nova Assistant")

    def _setup_detail_tabs(self, tabs: QTabWidget) -> None:
        """Setup detailed metric tabs with no selection highlighting"""
        # CPU Details
        cpu_widget = QWidget()
        cpu_layout = QVBoxLayout(cpu_widget)
        self.cpu_table = QTableWidget(12, 2)
        self.cpu_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.cpu_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cpu_table.setSelectionMode(QTableWidget.NoSelection)  # Disable selection
        self.cpu_table.setFocusPolicy(Qt.NoFocus)  # Remove focus highlighting
        
        cpu_header = self.cpu_table.horizontalHeader()
        for i in range(self.cpu_table.columnCount()):
            cpu_header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.cpu_table.verticalHeader().setVisible(False)
        
        cpu_metrics = [
            "CPU Usage", "CPU Frequency", "Logical Cores", "Physical Cores",
            "Load Average", "Context Switches", "Interrupts", "Syscalls",
            "User Time", "System Time", "Idle Time", "Temperature"
        ]
        for i, metric in enumerate(cpu_metrics):
            self.cpu_table.setItem(i, 0, QTableWidgetItem(metric))
            self.cpu_table.setItem(i, 1, QTableWidgetItem("--"))
        
        cpu_layout.addWidget(self.cpu_table)
        self.tabs.addTab(cpu_widget, "CPU Details")
        
        # Memory Details
        memory_widget = QWidget()
        memory_layout = QVBoxLayout(memory_widget)
        self.memory_table = QTableWidget(8, 2)
        self.memory_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.memory_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.memory_table.setSelectionMode(QTableWidget.NoSelection)  # Disable selection
        self.memory_table.setFocusPolicy(Qt.NoFocus)  # Remove focus highlighting
        
        memory_header = self.memory_table.horizontalHeader()
        for i in range(self.memory_table.columnCount()):
            memory_header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.memory_table.verticalHeader().setVisible(False)
        
        memory_metrics = [
            "Total Memory", "Available Memory", "Memory Usage", "Used Memory",
            "Swap Total", "Swap Used", "Swap Free", "Swap Usage"
        ]
        for i, metric in enumerate(memory_metrics):
            self.memory_table.setItem(i, 0, QTableWidgetItem(metric))
            self.memory_table.setItem(i, 1, QTableWidgetItem("--"))
        
        memory_layout.addWidget(self.memory_table)
        self.tabs.addTab(memory_widget, "Memory Details")
        
        # Disk Details
        disk_widget = QWidget()
        disk_layout = QVBoxLayout(disk_widget)
        self.disk_table = QTableWidget(10, 2)
        self.disk_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.disk_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.disk_table.setSelectionMode(QTableWidget.NoSelection)  # Disable selection
        self.disk_table.setFocusPolicy(Qt.NoFocus)  # Remove focus highlighting
        
        disk_header = self.disk_table.horizontalHeader()
        for i in range(self.disk_table.columnCount()):
            disk_header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.disk_table.verticalHeader().setVisible(False)
        
        disk_metrics = [
            "Total Space", "Used Space", "Free Space", "Usage",
            "Read Count", "Write Count", "Read Bytes", "Write Bytes",
            "Read Time", "Write Time"
        ]
        for i, metric in enumerate(disk_metrics):
            self.disk_table.setItem(i, 0, QTableWidgetItem(metric))
            self.disk_table.setItem(i, 1, QTableWidgetItem("--"))
        
        disk_layout.addWidget(self.disk_table)
        self.tabs.addTab(disk_widget, "Disk Details")
        
        # Network Details
        network_widget = QWidget()
        network_layout = QVBoxLayout(network_widget)
        self.network_table = QTableWidget(4, 2)
        self.network_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.network_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.network_table.setSelectionMode(QTableWidget.NoSelection)  # Disable selection
        self.network_table.setFocusPolicy(Qt.NoFocus)  # Remove focus highlighting
        
        network_header = self.network_table.horizontalHeader()
        for i in range(self.network_table.columnCount()):
            network_header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.network_table.verticalHeader().setVisible(False)
        
        network_metrics = ["Upload Speed", "Download Speed", "Total Sent", "Total Received"]
        for i, metric in enumerate(network_metrics):
            self.network_table.setItem(i, 0, QTableWidgetItem(metric))
            self.network_table.setItem(i, 1, QTableWidgetItem("--"))
        
        network_layout.addWidget(self.network_table)
        self.tabs.addTab(network_widget, "Network Details")
        
        # Battery Details
        battery_widget = QWidget()
        battery_layout = QVBoxLayout(battery_widget)
        self.battery_table = QTableWidget(3, 2)
        self.battery_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.battery_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.battery_table.setSelectionMode(QTableWidget.NoSelection)  # Disable selection
        self.battery_table.setFocusPolicy(Qt.NoFocus)  # Remove focus highlighting
        
        battery_header = self.battery_table.horizontalHeader()
        for i in range(self.battery_table.columnCount()):
            battery_header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.battery_table.verticalHeader().setVisible(False)
        
        battery_metrics = ["Battery Percentage", "Status", "Time Remaining"]
        for i, metric in enumerate(battery_metrics):
            self.battery_table.setItem(i, 0, QTableWidgetItem(metric))
            self.battery_table.setItem(i, 1, QTableWidgetItem("--"))
        
        battery_layout.addWidget(self.battery_table)
        self.tabs.addTab(battery_widget, "Battery Details")

    def _setup_processes_tab(self, tabs: QTabWidget) -> None:
        """Setup processes tab"""
        processes_widget = QWidget()
        processes_layout = QVBoxLayout(processes_widget)
        
        # Process controls
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignRight)
        
        self.show_all_button = QPushButton("Show More")
        self.show_all_button.setMaximumWidth(130)
        self.show_all_button.setFixedHeight(30)
        self.show_all_button.clicked.connect(self.toggle_process_view)
        self.show_all_processes = False
        
        button_layout.addWidget(self.show_all_button)
        processes_layout.addWidget(button_container)
        
        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "Status", "CPU %", "Memory %", "Created"
        ])
        self.process_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.process_table.setSelectionMode(QTableWidget.NoSelection)
        self.process_table.setFocusPolicy(Qt.NoFocus)

        process_header = self.process_table.horizontalHeader()
        for i in range(self.process_table.columnCount()):
            process_header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.process_table.verticalHeader().setVisible(False)
        
        processes_layout.addWidget(self.process_table)
        self.tabs.addTab(processes_widget, "Processes")


    def _setup_anomaly_tab(self, tabs: QTabWidget) -> None:
        """Setup anomaly detection tab"""
        anomaly_widget = QWidget()
        anomaly_layout = QVBoxLayout(anomaly_widget)
        
        # Anomaly status
        self.anomaly_status = QLabel("Ready to detect anomalies in system performance.")
        self.anomaly_status.setAlignment(Qt.AlignCenter)
        self.anomaly_status.setStyleSheet("font-size: 14px; padding: 10px;")
        
        # Detection controls
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignCenter)
        
        self.detect_button = QPushButton("Run Detection")
        self.detect_button.setFixedHeight(35)
        self.detect_button.clicked.connect(self.run_anomaly_detection)
        
        self.last_run_time = QLabel("Last run: Never")
        self.last_run_time.setStyleSheet("font-size: 12px; color: gray; padding: 5px;")
        
        button_layout.addWidget(self.detect_button)
        button_layout.addWidget(self.last_run_time)
        
        # Anomaly table
        self.anomaly_table = QTableWidget()
        self.anomaly_table.setColumnCount(4)
        self.anomaly_table.setHorizontalHeaderLabels([
            "Timestamp", "Type", "Value", "Severity"
        ])
        self.anomaly_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.anomaly_table.setSelectionMode(QTableWidget.NoSelection)
        self.anomaly_table.setFocusPolicy(Qt.NoFocus)
        
        anomaly_header = self.anomaly_table.horizontalHeader()
        for i in range(self.anomaly_table.columnCount()):
            anomaly_header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.anomaly_table.verticalHeader().setVisible(False)
        
        anomaly_layout.addWidget(self.anomaly_status)
        anomaly_layout.addWidget(button_container)
        anomaly_layout.addWidget(self.anomaly_table)
        self.tabs.addTab(anomaly_widget, "Anomaly Detection")

    def _setup_settings_tab(self, tabs: QTabWidget) -> None:
        """Setup settings tab"""
        self.settings_widget = QWidget()
        settings_layout = QVBoxLayout(self.settings_widget)
        
        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QHBoxLayout(theme_group)
        
        self.dark_button = QRadioButton("Dark Mode")
        self.dark_button.setChecked(True)
        self.dark_button.toggled.connect(self.set_dark_mode)
        
        self.light_button = QRadioButton("Light Mode")
        self.light_button.toggled.connect(self.set_light_mode)
        
        theme_layout.addWidget(self.dark_button)
        theme_layout.addWidget(self.light_button)
        
        # Command confirmation
        command_group = QGroupBox("Command Execution")
        command_layout = QVBoxLayout(command_group)
        
        self.confirm_checkbox = QCheckBox("Require confirmation before executing commands")
        self.confirm_checkbox.setChecked(self.FORCE_CONFIRM)
        self.confirm_checkbox.toggled.connect(self.toggle_command_confirmation)
        command_layout.addWidget(self.confirm_checkbox)
        
        # Background running
        background_group = QGroupBox("Background Running")
        background_layout = QVBoxLayout(background_group)
        
        self.background_checkbox = QCheckBox("Run in background")
        self.background_checkbox.setChecked(True)
        background_layout.addWidget(self.background_checkbox)
        
        settings_layout.addWidget(theme_group)
        settings_layout.addWidget(command_group)
        settings_layout.addWidget(background_group)
        settings_layout.addStretch()
        
        self.tabs.addTab(self.settings_widget, "Settings")

    def init_voice_recognition(self):
        """Initialize voice recognition components"""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
    def toggle_voice_input_mode(self):
        """Toggle continuous voice input mode"""
        self.VOICE_INPUT_MODE = not self.VOICE_INPUT_MODE
        
        # Update button appearance
        if self.VOICE_INPUT_MODE:
            self.nova_status.setText("Voice input activated")
            self.microphone_button.setStyleSheet("background-color: #4A90E2; color: white;")
            self.start_voice_listening()
        else:
            self.microphone_button.setStyleSheet("")
            self.nova_status.setText("Voice input deactivated")
            self.stop_voice_listening()
            
        # Update status
        status = "activated" if self.VOICE_INPUT_MODE else "deactivated"
        self.nova_status.setText(f"Voice input {status}.")

    def start_voice_listening(self):
        """Start continuous listening using the library's background feature."""
        if self.is_listening:
            return

        if not self.recognizer:
            self.init_voice_recognition()
        
        # The callback function that will be called on a background thread
        # when speech is detected.
        def recognition_callback(recognizer, audio):
            try:
                # The recognition is now done inside the callback
                text = recognizer.recognize_google(audio)
                # We need to emit a signal to pass the result to the main thread
                self.voice_input_received.emit(text)
            except sr.UnknownValueError:
                # This is common (silence), so we can just ignore it.
                pass
            except sr.RequestError as e:
                # API is unreachable or other issue.
                print(f"Voice recognition API error: {e}")
                self.voice_input_received.emit("") # Emit empty to avoid blocking

        # Start listening in the background. This returns a function to stop it.
        self.stop_listening_callback = self.recognizer.listen_in_background(
            self.microphone, recognition_callback
        )
        self.is_listening = True
        self.nova_status.setText("Listening...")
        print("Background voice listening started.")

    def stop_voice_listening(self):
        """Stop the background voice listener."""
        if self.stop_listening_callback:
            # Call the function returned by listen_in_background to stop it.
            # wait_for_stop=False makes it non-blocking.
            self.stop_listening_callback(wait_for_stop=False)
            self.stop_listening_callback = None
            self.is_listening = False
            print("Background voice listening stopped.")

        if not self.VOICE_INPUT_MODE:
            self.nova_status.setText("Voice input deactivated")
        else:
            self.nova_status.setText("Voice input paused")
            
    @pyqtSlot(str)
    def handle_voice_input(self, text: str):
        """Handle recognized voice input received from the signal."""
        if text:
            self.nova_input.setText(text)
            self.send_nova_command()

    def _cleanup_nova_worker(self) -> None:
        """Clean up Nova worker and thread safely"""
        try:
            # Clean up worker
            if hasattr(self, 'nova_worker') and self.nova_worker is not None:
                try:
                    self.nova_worker.deleteLater()
                except RuntimeError:
                    pass  # Already deleted
                self.nova_worker = None
            
            # Clean up thread after a small delay to ensure worker is cleaned up first
            QTimer.singleShot(100, self._cleanup_nova_thread)
            
        except Exception as e:
            print(f"Error cleaning up Nova worker: {e}")

    def _cleanup_nova_thread(self) -> None:
        """Clean up Nova thread safely"""
        try:
            if hasattr(self, 'nova_thread') and self.nova_thread is not None:
                try:
                    if not self.nova_thread.isFinished():
                        self.nova_thread.quit()
                        self.nova_thread.wait(1000)
                    self.nova_thread.deleteLater()
                except RuntimeError:
                    pass  # Already deleted
                self.nova_thread = None
                
        except Exception as e:
            print(f"Error cleaning up Nova thread: {e}")
            
    def switch_to_nova_tab(self) -> None:
        """Switch to Nova Assistant tab programmatically"""
        try:
            # Find the Nova tab index and switch to it
            for i in range(self.tabs.count() if hasattr(self, 'tabs') else 0):
                tab_text = self.tabs.tabText(i).lower()
                if 'nova' in tab_text or 'assistant' in tab_text:
                    self.tabs.setCurrentIndex(i)
                    print("Switched to Nova Assistant tab")
                    return
            print("Nova Assistant tab not found")
        except Exception as e:
            print(f"Error switching to Nova tab: {e}")

    def quit_application(self) -> None:
        """Quit the application completely - called by system tray"""
        try:
            # Hide system tray first
            if hasattr(self, 'system_tray') and self.system_tray:
                self.system_tray.hide_tray_icon()
            
            # Close the application
            QApplication.quit()
            
        except Exception as e:
            print(f"Error during application quit: {e}")        

    def cleanup_voice_thread(self):
        """Clean up voice recognition resources"""
        if hasattr(self, 'voice_thread') and self.voice_thread:
            try:
                self.voice_thread.quit()
                self.voice_thread.wait(500)
                self.voice_thread.deleteLater()
            except:
                pass
            finally:
                self.voice_thread = None
        self.voice_worker = None

    def _cleanup_threads(self):
        """Helper method to cleanup all threads"""
        # Nova thread cleanup
        if hasattr(self, 'nova_thread') and self.nova_thread is not None:
            try:
                if self.nova_thread.isRunning():
                    self.nova_thread.quit()
                    if not self.nova_thread.wait(3000):
                        self.nova_thread.terminate()
                        self.nova_thread.wait(1000)
            except RuntimeError:
                pass
            self.nova_thread = None
            self.nova_worker = None
                
        # TTS thread cleanup
        if hasattr(self, 'tts_thread') and self.tts_thread is not None:
            try:
                if self.tts_thread.isRunning():
                    self.tts_thread.quit()
                    if not self.tts_thread.wait(3000):
                        self.tts_thread.terminate()
                        self.tts_thread.wait(1000)
            except RuntimeError:
                pass
            self.tts_thread = None
            self.tts_worker = None

    def closeEvent(self, event):
        """Clean up all running threads and processes on application close."""
        print("Application closing, ensuring all threads are stopped.")
        
        self.stop_voice_listening()
        self._cleanup_nova_thread()
        
        # Check if background mode is enabled
        background_enabled = False
        if hasattr(self, 'background_checkbox'):
            background_enabled = self.background_checkbox.isChecked()
        
        # If background mode is enabled, minimize to tray instead of closing
        if background_enabled and hasattr(self, 'app_close_requested'):
            self.app_close_requested(True)
            event.ignore()
        else:
            # Perform full quit
            if hasattr(self, 'app_close_requested'):
                self.app_close_requested(False)
            event.accept()