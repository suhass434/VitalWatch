import psutil
import time
from datetime import datetime
import platform

class SystemMonitor:
    def __init__(self):
        """
        Initialize the SystemMonitor class.
        """
        self.matrix = {}
        self.is_windows = platform.system().lower() == 'windows'

    def get_cpu_metrics(self):
        """
        Collect CPU metrics.
        """
        temps = None if self.is_windows else psutil.sensors_temperatures()  # Only fetch temps on linux
        cpu_temp = temps['coretemp'][0].current if temps and 'coretemp' in temps else None

        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_temp': "--" if self.is_windows else cpu_temp,
            'cpu_freq': int(psutil.cpu_freq().current) if psutil.cpu_freq() else None,
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'cpu_count_physical': psutil.cpu_count(logical=False),
            'cpu_load_avg_1min': int(psutil.getloadavg()[0]) if hasattr(psutil, 'getloadavg') else None,
            'cpu_context_switches': psutil.cpu_stats().ctx_switches,
            'cpu_interrupts': psutil.cpu_stats().interrupts,
            'cpu_syscalls': psutil.cpu_stats().syscalls,
            'cpu_user_time': int(psutil.cpu_times().user),
            'cpu_system_time': int(psutil.cpu_times().system),
            'cpu_idle_time': int(psutil.cpu_times().idle)
        }

    def get_memory_metrics(self):
        """
        Collect memory metrics.
        """
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

    def get_network_metrics(self, interval=1):
        """
        Collect network metrics.
        """
        net_before = psutil.net_io_counters()
        time.sleep(interval)
        net_after = psutil.net_io_counters()

        bytes_sent_per_sec = (net_after.bytes_sent - net_before.bytes_sent) / interval
        bytes_recv_per_sec = (net_after.bytes_recv - net_before.bytes_recv) / interval

        return {
            'upload_speed': bytes_sent_per_sec,
            'download_speed': bytes_recv_per_sec,
            'total_data_sent': net_after.bytes_sent,
            'total_data_received': net_after.bytes_recv
        }
    
    def get_battery_metrics(self):
        battery = psutil.sensors_battery()
        if not battery:
            return "Battery information is not available on this system."

        percent = battery.percent
        charging = battery.power_plugged
        time_left = battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None

        status = "Charging" if charging else "Discharging"
        time_remaining = f"{time_left // 3600}h {time_left % 3600 // 60}m" if (time_left and int(time_left) < 100000) else "N/A"

        return {
            "battery_percentage": f"{percent:.2f}",
            "status": status,
            "time_remaining": time_remaining,
        }
    
    def collect_metrics(self):
        """
        Collect all system metrics.
        """
        self.metrics = {
            'timestamp': datetime.now(),
            'cpu': self.get_cpu_metrics(),
           'memory': self.get_memory_metrics(),
            'disk': self.get_disk_metrics(),
            'network': self.get_network_metrics(),
            'battery': self.get_battery_metrics()
        }
        return self.metrics
    

        
if __name__ == '__main__':
    s = SystemMonitor()
    metrics = s.collect_metrics()
    
    print(metrics)