import psutil
import yaml
from datetime import datetime
from heapq import nlargest

class ProcessMonitor:
    def __init__(self):
        self.processes = []
        self.config = self.load_config()

    def load_config(self):
        with open('config/config.yaml', 'r') as file:
            return yaml.safe_load(file)

    def get_process_info(self, process):
        try:
            create_time = datetime.fromtimestamp(process.create_time()).strftime('%d/%m/%Y %H:%M:%S')
            return {
                'pid': process.pid,
                'name': process.info['name'],
                'status': process.info['status'],
                'cpu_percent': process.info['cpu_percent'],
                'memory_percent': process.info['memory_percent'],
                'create_time': create_time
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None

    def monitor_processes(self, top_n=50, min_cpu=0.0):
        """
        Retrieve and filter the top `top_n` processes by CPU usage.
        """
        sleep_interval = self.config['monitoring']['process']['sleep']

        # generator with filtering
        process_info_gen = (
            self.get_process_info(proc)
            for proc in psutil.process_iter(
                ['name', 'status', 'cpu_percent', 'memory_percent', 'create_time']
            )
            # if proc.info['cpu_percent'] > min_cpu  
        )

        top_processes = nlargest(
            top_n,
            filter(None, process_info_gen),  # Filter out None entries
            key=lambda x: x['cpu_percent']
        )

        return top_processes
