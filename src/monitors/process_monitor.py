import psutil
import time
import yaml
from datetime import datetime

class ProcessMonitor:
    def __init__(self):
        self.processes = []

    def load_config(self):
        with open('config/config.yaml', 'r') as file:
            return yaml.safe_load(file)

    def get_process_info(self, process):
        try:
            config = self.load_config()
            time.sleep(config['monitoring']['process']['sleep'])
            create_time = datetime.fromtimestamp(process.create_time()).strftime('%d/%m/%Y %H:%M:%Sf')
            return {
                'pid': process.pid,
                'name': process.name(),
                'status': process.status(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'create_time': create_time
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                return None

    def monitor_processes(self):
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'create_time']):
            info = self.get_process_info(proc)
            if info:
                processes.append(info)
        return processes
