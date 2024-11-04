import psutil
import time
from datetime import datetime
import pynvml

class SystemMonitor:
    def __init__(self):
        self.matrix = {}

    def get_cpu_metrics(self):
        temps = psutil.sensors_temperatures()
        cpu_temp = temps['coretemp'][0].current if 'coretemp' in temps else None
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),  # Overall CPU usage as an integer
            'cpu_temp': cpu_temp,
            'cpu_freq': int(psutil.cpu_freq().current) if psutil.cpu_freq() else None,  # Current frequency
            'cpu_count_logical': psutil.cpu_count(logical=True),  # Logical core count
            'cpu_count_physical': psutil.cpu_count(logical=False),  # Physical core count
            'cpu_load_avg_1min': int(psutil.getloadavg()[0]) if hasattr(psutil, 'getloadavg') else None,  # Load avg (1 min)
            'cpu_context_switches': psutil.cpu_stats().ctx_switches,  # Context switches
            'cpu_interrupts': psutil.cpu_stats().interrupts,  # Interrupts
            'cpu_syscalls': psutil.cpu_stats().syscalls,  # System calls
            'cpu_user_time': int(psutil.cpu_times().user),  # User time in seconds
            'cpu_system_time': int(psutil.cpu_times().system),  # System time in seconds
            'cpu_idle_time': int(psutil.cpu_times().idle)  # Idle time in seconds
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
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        return {
            'gpu_load': pynvml.nvmlDeviceGetUtilizationRates(handle).gpu,
            'gpu_memory_total': pynvml.nvmlDeviceGetMemoryInfo(handle).total,
            'gpu_memory_used': pynvml.nvmlDeviceGetMemoryInfo(handle).used,
            'gpu_memory_free': pynvml.nvmlDeviceGetMemoryInfo(handle).free,
            'gpu_temperature': pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        }

    def get_cpu_load(self):
        cpu_load = psutil.cpu_percent(interval=1)        
        temps = psutil.sensors_temperatures()
        cpu_temp = temps['coretemp'][0].current if 'coretemp' in temps else None

        return {
            'cpu_load': cpu_load , 
            'cpu_temp': cpu_temp
        }

    def collect_metrics(self):
        self.metrics = {
            'timestamp': datetime.now(),
            'cpu': self.get_cpu_metrics(),
            'memory': self.get_memory_metrics(),
            'disk': self.get_disk_metrics(),
            'network': self.get_network_metrics(),
            'cpu_load': self.get_cpu_load()
        }
        return self.metrics