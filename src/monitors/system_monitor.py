import psutil
import time
from datetime import datetime
import GPUtil

class SystemMonitor:
    def __init__(self):
        self.matrix = {}

    def get_cpu_metrics(self):
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_freq': psutil.cpu_freq().current,
            'cpu_count': psutil.cpu_count(),
        }

    def get_memory_metrics(self):
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'percent': mem.percent,
            'used': mem.used
        }

    def get_disk_metrics(self):
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }

    def get_network_metrics(self,interval = 1):
        # Capture bytes sent/received at the start
        net_before = psutil.net_io_counters()
        time.sleep(interval)
        # Capture bytes sent/received after the interval
        net_after = psutil.net_io_counters()
        
        # Calculate the upload and download speeds
        bytes_sent_per_sec = (net_after.bytes_sent - net_before.bytes_sent) / interval
        bytes_recv_per_sec = (net_after.bytes_recv - net_before.bytes_recv) / interval
        return {
            'upload_speed': bytes_sent_per_sec,  # in bytes per second
            'download_speed': bytes_recv_per_sec,  # in bytes per second
            'total_data_sent': net_after.bytes_sent,  # total bytes sent
            'total_data_received': net_after.bytes_recv  # total bytes received
        }

    def get_gpu_metrics(self):
        gpus = GPUtil.getGPUs()
        if not gpus:
            print("No GPU found.")
            return None  # Return None if no GPU is available
        gpu = gpus[0]  # Using the first GPU for simplicity
        return {
            'gpu_load': gpu.load * 100,        # Load as a percentage
            'gpu_memory_total': gpu.memoryTotal,  # Total GPU memory
            'gpu_memory_used': gpu.memoryUsed,    # Used GPU memory
            'gpu_memory_free': gpu.memoryFree,    # Free GPU memory
            'gpu_temperature': gpu.temperature    # GPU temperature
        }

    def collect_metrics(self):
        self.metrics = {
            'timestamp': datetime.now(),
            'cpu': self.get_cpu_metrics(),
            'memory': self.get_memory_metrics(),
            'disk': self.get_disk_metrics(),
            'network': self.get_network_metrics(),
            'gpu': self.get_gpu_metrics()
        }
        return self.metrics