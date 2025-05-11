import subprocess
from .config import ACTION_WHITELIST, FILE_WHITELIST

def is_safe(command: dict) -> bool:
    if command["action"] not in ACTION_WHITELIST:
        return False
    if command["action"] == "open_file":
        return any(command["target"].startswith(p) for p in FILE_WHITELIST)
    return True

def execute(command: dict, dry_run: bool=False):
    assert is_safe(command), "Blocked unsafe command"
    
    if dry_run:
        print("[dry-run]", command)
        return None
        
    if command["action"] == "shutdown":
        subprocess.run(["shutdown", "-h", "now"], check=True)
        return "Shutdown initiated."
        
    if command["action"] == "open_file":
        subprocess.run(["xdg-open", command["target"]], check=True)
        return f"Opened file: {command['target']}"
        
    if command["action"] == "run_command":
        target_command = command["target"]
        
        # Detect if command should run in background
        is_background = target_command.strip().endswith('&')
        
        # Detect system info commands that should not run in background
        info_commands = ["inxi", "lscpu", "free", "df", "top", "ps", "neofetch", "systeminfo", "uname"]
        is_info_command = any(cmd in target_command for cmd in info_commands)
        
        # Remove trailing & for info commands to capture output
        if is_info_command and is_background:
            target_command = target_command.strip()[:-1].strip()
            is_background = False
        
        # Handle background processes differently
        if is_background and not is_info_command:
            # For background processes, use Popen and don't wait
            subprocess.Popen(
                target_command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # This detaches the process completely
            )
            return f"The {target_command.strip()[:-1]} command was successfully launched in the background."
        else:
            # For normal commands, use subprocess.run and capture output
            result = subprocess.run(
                target_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            return result.stdout
        
    raise RuntimeError("Unknown action")
