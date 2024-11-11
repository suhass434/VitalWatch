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
        swap_info = psutil.swap_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'percent': mem.percent,
            'used': mem.used,
            'swap_total': swap_info.total,
            'swap_used': swap_info.used,
            'swap_free': swap_info.free,
            'swap_percent': swap_info.percent            
        }

    def get_disk_metrics(self):
        total = 0
        used = 0
        free = 0
        percent = 0
        read_count = 0
        write_count = 0
        read_bytes = 0
        write_bytes = 0
        read_time = 0
        write_time = 0
        num_partitions = 0

        # Get total disk usage for the whole disk (root partition)
        try:
            total_usage = psutil.disk_usage('/')
            total = total_usage.total
            free = total_usage.free
            used = total_usage.used
            percent = total_usage.percent
        except Exception as e:
            print(f"Error getting total disk usage: {e}")

        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                io_counters = psutil.disk_io_counters(perdisk=True).get(partition.device.split('/')[-1])

                read_count += io_counters.read_count if io_counters else 0
                write_count += io_counters.write_count if io_counters else 0
                read_bytes += io_counters.read_bytes if io_counters else 0
                write_bytes += io_counters.write_bytes if io_counters else 0
                read_time += io_counters.read_time if io_counters else 0
                write_time += io_counters.write_time if io_counters else 0
                num_partitions += 1

            except (KeyError, PermissionError):
                continue

        # Return disk metrics
        disk_metrics = {
            'total': total,
            'used': used,
            'free': free,
            'percent': percent,
            'read_count': read_count,
            'write_count': write_count,
            'read_bytes': read_bytes,
            'write_bytes': write_bytes,
            'read_time': read_time,
            'write_time': write_time
        }

        return disk_metrics


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