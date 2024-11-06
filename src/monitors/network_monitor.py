import psutil
import time

class NetworkUsage:
    def get_network_usage(self, interval=1):
        # Capture bytes sent/received at the start
        net_before = psutil.net_io_counters()
        time.sleep(interval)
        # Capture bytes sent/received after the interval
        net_after = psutil.net_io_counters()

        # Calculate the upload and download speeds
        bytes_sent_per_sec = (net_after.bytes_sent - net_before.bytes_sent) / interval
        bytes_recv_per_sec = (net_after.bytes_recv - net_before.bytes_recv) / interval
        
        # # Additional metrics
        # packets_sent = net_after.packets_sent - net_before.packets_sent
        # packets_recv = net_after.packets_recv - net_before.packets_recv
        # errors_sent = net_after.errout - net_before.errout
        # errors_recv = net_after.errin - net_before.errin
        #print(errors_sent)
        return {
            'upload_speed': bytes_sent_per_sec / 1024,  # in kb per second
            'download_speed': bytes_recv_per_sec / 1024,  # in kb per second
            'total_data_sent': net_after.bytes_sent / 1024,  # total kb sent
            'total_data_received': net_after.bytes_recv / 1024  # total kb received
            # 'packets_sent': packets_sent,
            # 'packets_received': packets_recv,
            # 'errors_sent': errors_sent,
            # 'errors_received': errors_recv,
        }