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
        # Capture stdout
        result = subprocess.run(
            command["target"],
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return result.stdout

    raise RuntimeError("Unknown action")