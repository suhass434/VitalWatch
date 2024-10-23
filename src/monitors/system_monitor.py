import psutil
import time
from datetime import datetime
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
    
    def collect_metrics(self):
        self.metrics = {
            'timestamp': datetime.now(),
            'cpu': self.get_cpu_metrics(),
            'memory': self.get_memory_metrics(),
            'disk': self.get_disk_metrics()
        }
        return self.metrics