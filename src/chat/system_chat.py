from transformers import pipeline
from src.monitors.system_monitor import SystemMonitor
from src.monitors.process_monitor import ProcessMonitor
from src.database.db_handler import DatabaseHandler
from src.alerts.alert_manager import AlertManager
from src.recovery.recovery_actions import RecoveryManager
import psutil

class SystemChat:
    def __init__(self):
        self.nlp = pipeline("text2text-generation", model="google/flan-t5-small")
        
    def process_query(self, user_input):
        if "cpu" in user_input.lower():
            return f"Current CPU usage is {psutil.cpu_percent()}%"
        elif "memory" in user_input.lower():
            mem = psutil.virtual_memory()
            return f"Memory usage: {mem.percent}% used, {mem.available/1024/1024:.2f}MB available"
        elif "status" in user_input.lower():
            return self.get_system_status()
            
    def get_system_status(self):
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return f"System Status:\nCPU: {cpu}%\nMemory: {memory}%\nDisk: {disk}%"