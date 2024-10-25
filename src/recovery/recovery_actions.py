import psutil
import os
import subprocess

class RecoveryManager:
    def __init__(self):
        self.recovery_actions = {
            'high_cpu': self.handle_high_cpu,
            'high_memory': self.handle_high_memory,
            'service_down': self.restart_service
        }
    
    def handle_high_cpu(self):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if proc.cpu_percent() > 80:
                    processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        for proc in sorted(processes, key=lambda p: p.cpu_percent(), reverse=True)[:1]:
            try:
                proc.terminate()
                return f"Terminated high CPU process: {proc.name()}"
            except:
                return "Failed to terminate process"
    
    def handle_high_memory(self):
        os.system('sync; echo 3 > /proc/sys/vm/drop_caches')
        return "Cleared system cache"
    
    def restart_service(self, service_name):
        try:
            subprocess.run(['systemctl', 'restart', service_name])
            return f"Restarted service: {service_name}"
        except:
            return f"Failed to restart service: {service_name}"