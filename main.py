import time
from src.monitors.system_monitor import SystemMonitor
from src.monitors.process_monitor import ProcessMonitor
from src.database.db_handler import DatabaseHandler
from src.alerts.alert_manager import AlertManager
from src.recovery.recovery_actions import RecoveryManager
import yaml

#from src.chat.system_chat import SystemChat
#import threading

def load_config():
    with open('config/config.yaml', 'r') as file:
        return yaml.safe_load(file)

def main():
    # Initialize components
    config = load_config()
    system_monitor = SystemMonitor()
    process_monitor = ProcessMonitor()
    db_handler = DatabaseHandler()
    alert_manager = AlertManager(config)
    recovery_manager = RecoveryManager()
    
    # # Start chat interface in a separate thread
    # chat_thread = threading.Thread(target=chat_interface, daemon=True)
    # chat_thread.start()
    
    last_backup_time = time.time()
    backup_interval = config['database']['backup_interval']

    while True:
        try:
            current_time = time.time()
            # Collect metrics
            metrics = system_monitor.collect_metrics()
            processes = process_monitor.monitor_processes()
            
            # Store metrics
            db_handler.store_metrics(metrics)
            
            # Check for issues
            if metrics['cpu']['cpu_percent'] > config['monitoring']['thresholds']['cpu']:
                print(f'{config['monitoring']['thresholds']['cpu']}')
                alert_manager.send_slack_alert("High CPU Usage Detected!")
                recovery_manager.handle_high_cpu()
            
            if metrics['memory']['percent'] > config['monitoring']['thresholds']['memory']:
                print(f'{config['monitoring']['thresholds']['memory']}')
                alert_manager.send_slack_alert("High Memory Usage Detected!")
                recovery_manager.handle_high_memory()

            if metrics['disk']['percent'] > config['monitoring']['thresholds']['disk']:
                print(f'{config['monitoring']['thresholds']['disk']}')
                alert_manager.send_slack_alert("High Memory Usage Detected!")
                recovery_manager.handle_high_memory()

            if current_time-last_backup_time >= backup_interval:
                db_handler.backup_database(config['backup']['path'])
                last_backup_time = current_time

            # Wait for next iteration
            time.sleep(config['monitoring']['interval'])
            
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            time.sleep(config['monitoring']['interval'])

# def chat_interface():
#     system_chat = SystemChat()
#     while True:
#         user_input = input("Ask about system status (or 'exit' to quit): ")
#         if user_input.lower() == 'exit':
#             break
#         response = system_chat.process_query(user_input)
#         print(response)
if __name__ == "__main__":
    main()